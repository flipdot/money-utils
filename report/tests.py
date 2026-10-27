from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from report.models import FeeEntry, Member, Transaction
from schema.fee_util import PayInterval


class MembersPerMonthViewTest(TestCase):
    """The view feeds FeeEntry querysets into pandas and then bokeh, so a
    dependency bump on either side (e.g. pandas 2 -> 3, PR #87) can break
    rendering without touching this app's code. Keep this rendering test
    passing when upgrading pandas or bokeh."""

    @classmethod
    def setUpTestData(cls):
        member = Member.objects.create(
            first_name='Test',
            last_name='Person',
            nick='tester',
            pay_interval=PayInterval.MONTHLY,
        )
        # The view slices the first and last month off (df.iloc[1:-1]),
        # so use enough months for the chart to have data left.
        months = [date(2024, month, 15) for month in (1, 2, 3, 4)]
        for i, month in enumerate(months):
            tx = Transaction.objects.create(
                date=month,
                amount=Decimal('10.00'),
                purpose=f'membership fee {month:%Y-%m}',
            )
            FeeEntry.objects.create(
                member=member,
                month=month,
                tx=tx,
                fee=Decimal('2.50') + i * Decimal('0.50'),
                pay_interval=PayInterval.MONTHLY,
            )

    def test_view_renders_months(self):
        response = self.client.get(reverse('report:members_per_month'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # The bokeh document embedded in the response must contain the
        # month factors of the middle months.
        self.assertIn('2024-02', content)
        self.assertIn('2024-03', content)


class MembersPerMonthSparseDataTest(TestCase):
    """The view slices the first and last month off (df.iloc[1:-1]), so
    fewer than three months of FeeEntry rows leave nothing to plot. A fresh
    installation has no rows at all and must render, not 500."""

    def _create_month(self, member, month):
        tx = Transaction.objects.create(
            date=month,
            amount=Decimal('10.00'),
            purpose=f'membership fee {month:%Y-%m}',
        )
        FeeEntry.objects.create(
            member=member,
            month=month,
            tx=tx,
            fee=Decimal('2.50'),
            pay_interval=PayInterval.MONTHLY,
        )

    def test_view_renders_without_fee_entries(self):
        response = self.client.get(reverse('report:members_per_month'))
        self.assertEqual(response.status_code, 200)

    def test_view_renders_with_two_months(self):
        member = Member.objects.create(
            first_name='Test',
            last_name='Person',
            nick='tester',
            pay_interval=PayInterval.MONTHLY,
        )
        self._create_month(member, date(2024, 1, 15))
        self._create_month(member, date(2024, 2, 15))
        response = self.client.get(reverse('report:members_per_month'))
        self.assertEqual(response.status_code, 200)
