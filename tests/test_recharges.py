"""Tests for the drink-recharge report and the drinks transaction filter.

``/recharges.json`` feeds the bar's recharge system, and
``drinks_transactions`` decides what counts as drinks income.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from report.get_recharges import get_recharges
from report.models import Transaction
from report.views import drinks_transactions


class GetRechargesTest(TestCase):
    def setUp(self):
        self.txs = {
            'earlier': Transaction.objects.create(
                date=date(2024, 1, 5), amount=Decimal('5.00'),
                purpose='drinks 123 max foo'),
            'later': Transaction.objects.create(
                date=date(2024, 1, 3), amount=Decimal('10.00'),
                purpose='drinks 123'),
            'other': Transaction.objects.create(
                date=date(2024, 1, 6), amount=Decimal('10.00'),
                purpose='drink 456 bar baz'),
            'non_drinks': Transaction.objects.create(
                date=date(2024, 1, 7), amount=Decimal('10.00'),
                purpose='Miete 23'),
        }

    def test_groups_by_uid_and_sorts_by_date(self):
        recharges = get_recharges()
        self.assertEqual(set(recharges), {'123', '456'})
        self.assertEqual([r['date'] for r in recharges['123']],
                         ['2024-01-03', '2024-01-05'])
        self.assertEqual(len(recharges['456']), 1)

    def test_entry_fields(self):
        recharges = get_recharges()
        entry = recharges['456'][0]
        self.assertEqual(entry['uid'], '456')
        self.assertEqual(entry['amount'], '10.00')
        self.assertEqual(entry['date'], '2024-01-06')
        self.assertEqual(len(entry['info']), 40)  # sha1 hexdigest

    def test_case_insensitive(self):
        Transaction.objects.create(date=date(2024, 1, 8),
                                   amount=Decimal('5.00'),
                                   purpose='Drinks 789')
        self.assertIn('789', get_recharges())


class DrinksTransactionsFilterTest(TestCase):
    def setUp(self):
        self.included = {
            'edeka_purpose': Transaction.objects.create(
                date=date(2024, 1, 1), amount=Decimal('100.00'),
                purpose='edeka einkauf'),
            'edeka_applicant': Transaction.objects.create(
                date=date(2024, 1, 2), amount=Decimal('100.00'),
                applicant_name='edeka kasse', purpose='Wareneingang'),
            'drinks_prefix': Transaction.objects.create(
                date=date(2024, 1, 3), amount=Decimal('5.00'),
                purpose='drinks 123'),
            'sb_einzahlung': Transaction.objects.create(
                date=date(2024, 1, 4), amount=Decimal('20.00'),
                purpose='sb-einzahlung'),
            'kleingeld': Transaction.objects.create(
                date=date(2024, 1, 5), amount=Decimal('12.34'),
                purpose='UNGEZaeHLTES KLEINGELD'),
            'getraenkeverkauf': Transaction.objects.create(
                date=date(2024, 1, 6), amount=Decimal('33.00'),
                purpose='EINNAHMEN GETRAENKEVERKAUF'),
        }
        self.excluded = Transaction.objects.create(
            date=date(2024, 1, 7), amount=Decimal('10.00'),
            purpose='Miete 23')

    def test_filter_selects_exactly_the_drinks_transactions(self):
        found = [tx for tx in drinks_transactions()]
        self.assertEqual({t.purpose for t in found},
                         {t.purpose for t in self.included.values()})
        self.assertNotIn(self.excluded.tx_id, [t.tx_id for t in found])

    def test_filter_is_ordered_by_date(self):
        purposes = [tx.purpose for tx in drinks_transactions()]
        self.assertEqual(purposes, [
            'edeka einkauf', 'Wareneingang', 'drinks 123',
            'sb-einzahlung', 'UNGEZaeHLTES KLEINGELD', 'EINNAHMEN GETRAENKEVERKAUF',
        ])
