"""Tests for ``split_into_entries``: how one bank transfer becomes fee entries.

This function decides how much a member paid for which months. A wrong split
means the club's books show the wrong income and the wrong member status.
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from members import split_into_entries
from schema.fee_util import DetectMethod, PayInterval
from schema.transaction import Transaction
from tests.helpers import fake_amount, make_tx


def member(fee=None, last_fee=None, id=1):
    return SimpleNamespace(id=id, fee=fee, last_fee=last_fee)


def entries_for(tx, mem):
    # The session is not used by split_into_entries itself.
    return split_into_entries(mem, None, Transaction(tx))


def assert_split(entries, expected_months, fee, detect, interval):
    assert len(entries) == len(expected_months)
    for entry, month in zip(entries, expected_months):
        assert entry.month == month, entry.month
        assert entry.fee == fee, entry.fee
        assert entry.detect_method == detect
        assert entry.pay_interval == interval
        assert entry.member_id == 1
        assert entry.tx is not None


class TestDetectionPriority:
    def test_fee_command_beats_exact_fee_amount(self):
        # 23.00 is a known fee amount, but an explicit month command must win.
        tx = make_tx(amount=fake_amount('23.00'), date=date(2024, 1, 10),
                     entry_date=date(2024, 1, 10), purpose='Miete 2024-01 - 2024-02')
        entries = entries_for(tx, member(fee=Decimal('23.00')))
        assert_split(entries,
                     [date(2024, 1, 1), date(2024, 2, 1)],
                     Decimal('11.50'), DetectMethod.FEE_COMMAND, PayInterval.VARIABLE)

    def test_exact_fee_amount(self):
        tx = make_tx(amount=fake_amount('23.00'), date=date(2024, 1, 10),
                     entry_date=date(2024, 1, 10), purpose='Miete')
        entries = entries_for(tx, member())
        assert_split(entries, [date(2024, 1, 1)],
                     Decimal('23.00'), DetectMethod.LAST_FEE, PayInterval.MONTHLY)

    def test_multiple_of_members_fee_wins_over_common_fee(self):
        # 138.00 is both 12 * 11.50 (the member's fee) and 6 * 23 (a common
        # fee). The member-specific multiple must win.
        tx = make_tx(amount=fake_amount('138.00'), date=date(2024, 1, 10),
                     entry_date=date(2024, 1, 10), purpose='Halbjahresbeitrag')
        entries = entries_for(tx, member(fee=Decimal('11.50')))
        assert len(entries) == 12
        assert all(e.fee == Decimal('11.50') for e in entries)
        assert all(e.detect_method == DetectMethod.MULTIPLE_OF_FEE for e in entries)
        assert all(e.pay_interval == PayInterval.YEARLY for e in entries)

    def test_fallback(self):
        # 7.77 matches nothing: it must not be split, just recorded as-is.
        tx = make_tx(amount=fake_amount('7.77'), date=date(2024, 1, 10),
                     entry_date=date(2024, 1, 10), purpose='Miete')
        entries = entries_for(tx, member(fee=Decimal('23.00')))
        assert_split(entries, [date(2024, 1, 1)],
                     Decimal('7.77'), DetectMethod.FALLBACK, PayInterval.MONTHLY)


class TestSplitting:
    def test_fee_command_range_is_split_evenly(self):
        tx = make_tx(amount=fake_amount('36.00'), date=date(2024, 1, 10),
                     entry_date=date(2024, 1, 10), purpose='Miete 2024-01 - 2024-03')
        entries = entries_for(tx, member())
        assert_split(entries,
                     [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)],
                     Decimal('12.00'), DetectMethod.FEE_COMMAND, PayInterval.VARIABLE)

    def test_fee_command_single_month(self):
        tx = make_tx(amount=fake_amount('10.00'), date=date(2024, 1, 10),
                     entry_date=date(2024, 1, 10), purpose='Miete 2024-05')
        entries = entries_for(tx, member())
        assert_split(entries, [date(2024, 5, 1)],
                     Decimal('10.00'), DetectMethod.FEE_COMMAND, PayInterval.VARIABLE)

    def test_yearly_multiple_of_common_fee(self):
        # 120.00 = 12 * 10.00 (student fee); no member-specific fee set.
        tx = make_tx(amount=fake_amount('120.00'), date=date(2024, 1, 5),
                     entry_date=date(2024, 1, 5), purpose='Jahresbeitrag')
        entries = entries_for(tx, member())
        months = [date(2024, m, 1) for m in range(1, 13)]
        assert_split(entries, months, Decimal('10.00'),
                     DetectMethod.MULTIPLE_OF_COMMON_FEE, PayInterval.YEARLY)

    def test_half_year_multiple_of_common_fee(self):
        # 138.00 = 6 * 23.00 (regular fee)
        tx = make_tx(amount=fake_amount('138.00'), date=date(2024, 1, 5),
                     entry_date=date(2024, 1, 5), purpose='Halbjahresbeitrag')
        entries = entries_for(tx, member())
        months = [date(2024, m, 1) for m in range(1, 7)]
        assert_split(entries, months, Decimal('23.00'),
                     DetectMethod.MULTIPLE_OF_COMMON_FEE, PayInterval.SIX_MONTH)

    def test_split_of_members_fee_yearly(self):
        # 138.00 = 12 * 11.50 (member's individual fee)
        tx = make_tx(amount=fake_amount('138.00'), date=date(2024, 1, 5),
                     entry_date=date(2024, 1, 5), purpose='Jahresbeitrag')
        entries = entries_for(tx, member(fee=Decimal('11.50')))
        assert len(entries) == 12
        assert sum(e.fee for e in entries) == Decimal('138.00')

    def test_split_of_members_fee_half_year(self):
        # 69.00 = 6 * 11.50
        tx = make_tx(amount=fake_amount('69.00'), date=date(2024, 1, 5),
                     entry_date=date(2024, 1, 5), purpose='Halbjahresbeitrag')
        entries = entries_for(tx, member(fee=Decimal('11.50')))
        months = [date(2024, m, 1) for m in range(1, 7)]
        assert_split(entries, months, Decimal('11.50'),
                     DetectMethod.MULTIPLE_OF_FEE, PayInterval.SIX_MONTH)

    def test_split_sums_to_paid_amount(self):
        for paid, parts in [('36.00', 3), ('120.00', 12), ('138.00', 6),
                            ('60.00', 6), ('216.00', 6), ('180.00', 12)]:
            tx = make_tx(amount=fake_amount(paid), date=date(2024, 1, 5),
                         entry_date=date(2024, 1, 5), purpose='Beitrag')
            entries = entries_for(tx, member())
            assert sum(e.fee for e in entries) == Decimal(paid), paid


class TestCrossover:
    def test_payment_before_crossover_counts_for_same_month(self):
        # crossover_days is 10 in config: a payment on the 20th is current month
        tx = make_tx(amount=fake_amount('23.00'), date=date(2024, 1, 20),
                     entry_date=date(2024, 1, 20), purpose='Miete')
        entries = entries_for(tx, member())
        assert entries[0].month == date(2024, 1, 1)

    def test_payment_after_crossover_counts_for_next_month(self):
        # a payment on the 29th belongs to the following month
        tx = make_tx(amount=fake_amount('23.00'), date=date(2024, 1, 29),
                     entry_date=date(2024, 1, 29), purpose='Miete')
        entries = entries_for(tx, member())
        assert entries[0].month == date(2024, 2, 1)
