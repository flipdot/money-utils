"""Tests for the Django models of the web app.

These models share their database file with the SQLAlchemy importer, so the
identity rules and constraints here must hold up against real re-imports.
"""
from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction as django_transaction
from django.test import TestCase

from report.models import FeeEntry, Member, Transaction
from schema.fee_util import PayInterval


class TransactionIdentityTest(TestCase):
    def test_save_generates_stable_id(self):
        t1 = Transaction(date=date(2024, 1, 15), amount=Decimal('10.00'),
                         purpose='Miete max')
        t2 = Transaction(date=date(2024, 1, 15), amount=Decimal('10.00'),
                         purpose='Miete max')
        self.assertEqual(t1.gen_id(), t2.gen_id())

    def test_save_persists_generated_id(self):
        tx = Transaction(date=date(2024, 1, 15), amount=Decimal('10.00'),
                         purpose='Miete max')
        expected = tx.gen_id()
        tx.save()
        self.assertEqual(tx.tx_id, expected)
        self.assertEqual(Transaction.objects.get().tx_id, expected)

    def test_different_purpose_different_id(self):
        t1 = Transaction(date=date(2024, 1, 15), amount=Decimal('10.00'),
                         purpose='Miete max')
        t2 = Transaction(date=date(2024, 1, 15), amount=Decimal('10.00'),
                         purpose='Spende max')
        self.assertNotEqual(t1.gen_id(), t2.gen_id())


class FeeEntryModelTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(
            first_name='Max', last_name='Mustermann', nick='max',
            pay_interval=PayInterval.MONTHLY)
        self.tx = Transaction.objects.create(
            date=date(2024, 1, 15), amount=Decimal('10.00'),
            purpose='Miete max')

    def test_save_composes_id_from_member_and_month(self):
        entry = FeeEntry(member=self.member, month=date(2024, 1, 1),
                         tx=self.tx, fee=Decimal('10.00'),
                         pay_interval=PayInterval.MONTHLY)
        entry.save()
        self.assertEqual(entry.id, f"{self.member.id}|2024-01-01")

    def test_one_entry_per_member_and_month(self):
        FeeEntry.objects.create(member=self.member, month=date(2024, 1, 1),
                                tx=self.tx, fee=Decimal('10.00'),
                                pay_interval=PayInterval.MONTHLY)
        with self.assertRaises(IntegrityError):
            with django_transaction.atomic():
                FeeEntry.objects.create(member=self.member, month=date(2024, 1, 1),
                                        tx=self.tx, fee=Decimal('10.00'),
                                        pay_interval=PayInterval.MONTHLY)

    def test_same_member_different_months_allowed(self):
        for month in (date(2024, 1, 1), date(2024, 2, 1)):
            FeeEntry.objects.create(member=self.member, month=month,
                                    tx=self.tx, fee=Decimal('10.00'),
                                    pay_interval=PayInterval.MONTHLY)
        self.assertEqual(FeeEntry.objects.count(), 2)


class MemberModelTest(TestCase):
    def test_is_member(self):
        member = Member.objects.create(first_name='Max', last_name='M',
                                       nick='', pay_interval=PayInterval.MONTHLY)
        self.assertTrue(member.is_member())
        member.exit_date = date(2024, 2, 9)
        member.save()
        self.assertFalse(member.is_member())
