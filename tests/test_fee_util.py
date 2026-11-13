"""Tests for the month patterns that decide which month a fee counts for.

These regexes and ``month_command`` are the heart of the fee analysis: a
misparse silently attributes a real payment to the wrong month (or drops it).
"""
from datetime import date
from types import SimpleNamespace

from members import month_command, month_command_ymd


def tx(purpose, tx_date):
    return SimpleNamespace(purpose=purpose, date=tx_date)


class TestFeeAmounts:
    def test_fee_amounts_values(self):
        # Pin the fee table: the whole analysis branches on these amounts.
        from schema.fee_util import fee_amounts
        assert set(fee_amounts) == {1, 3, 5, 10, 15, 18, 23, 36}

    def test_common_fee_amounts_values(self):
        from schema.fee_util import common_fee_amounts
        assert set(common_fee_amounts) == {10, 23, 36}


class TestMonthCommandYmd:
    def test_iso_range(self):
        months = list(month_command_ymd('Miete 2024-01 - 2024-03'))
        assert months == [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)]

    def test_iso_range_single_month(self):
        months = list(month_command_ymd('Miete 2024-02 - 2024-02'))
        assert months == [date(2024, 2, 1)]

    def test_single_ymd(self):
        assert list(month_command_ymd('Beitrag 2024-02')) == [date(2024, 2, 1)]

    def test_several_ymd(self):
        assert list(month_command_ymd('2024-01 2024-02')) == [date(2024, 1, 1), date(2024, 2, 1)]

    def test_full_date_is_not_a_month_command(self):
        # "2024-02-10" is a date, not a month: it must not match.
        assert list(month_command_ymd('Miete 2024-02-10')) == []

    def test_ym_pattern_parses_year_as_written(self):
        # "MM/YYYY" uses the 4-digit year as written (issue #111).
        assert list(month_command_ymd('Beitrag 03/2024')) == [date(2024, 3, 1)]

    def test_german_month_name(self):
        assert list(month_command_ymd('Miete Januar 2024')) == [date(2024, 1, 1)]

    def test_german_month_name_maerz(self):
        assert list(month_command_ymd('Miete Maerz 2025')) == [date(2025, 3, 1)]

    def test_german_month_name_at_end_of_text(self):
        assert list(month_command_ymd('max Januar 2024')) == [date(2024, 1, 1)]

    def test_no_pattern(self):
        assert list(month_command_ymd('Miete max')) == []


class TestMonthCommand:
    """month_command adds a plausibility range around the tx date."""

    def test_in_range(self):
        months = month_command(tx('Beitrag 2024-06', date(2024, 1, 1)))
        assert months == [date(2024, 6, 1)]

    def test_far_future_is_rejected(self):
        # more than 2 years after the tx date: must be ignored
        assert month_command(tx('Beitrag 2026-06', date(2024, 1, 1))) is None

    def test_ym_pattern_is_accepted_in_range(self):
        assert month_command(tx('Beitrag 03/2024', date(2024, 1, 1))) == \
            [date(2024, 3, 1)]

    def test_far_past_is_rejected(self):
        # more than 1 year before the tx date: must be ignored
        assert month_command(tx('Beitrag 2022-06', date(2024, 1, 1))) is None

    def test_range_with_one_out_of_range_month_is_rejected(self):
        assert month_command(
            tx('2024-01 - 2026-06', date(2024, 1, 1))) is None

    def test_no_pattern(self):
        assert month_command(tx('Miete max', date(2024, 1, 1))) is None
