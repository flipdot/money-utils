"""Tests for the month iteration used across the analysis and reports."""
from datetime import date

from util import months, months_german


def test_months_iterates_inclusive_of_both_ends():
    assert list(months(date(2024, 1, 15), date(2024, 3, 10))) == [
        (date(2024, 1, 1), date(2024, 2, 1)),
        (date(2024, 2, 1), date(2024, 3, 1)),
        (date(2024, 3, 1), date(2024, 4, 1)),
    ]


def test_months_same_month():
    assert list(months(date(2024, 2, 1), date(2024, 2, 28))) == [
        (date(2024, 2, 1), date(2024, 3, 1))]


def test_months_across_year_boundary():
    assert list(months(date(2023, 12, 5), date(2024, 1, 10))) == [
        (date(2023, 12, 1), date(2024, 1, 1)),
        (date(2024, 1, 1), date(2024, 2, 1)),
    ]


def test_months_empty_when_from_after_to():
    assert list(months(date(2024, 3, 1), date(2024, 1, 15))) == []


def test_german_month_numbers():
    assert months_german == {
        'Januar': 1, 'Februar': 2, 'Maerz': 3, 'April': 4,
        'Mai': 5, 'Juni': 6, 'Juli': 7, 'August': 8,
        'September': 9, 'Oktober': 10, 'November': 11, 'Dezember': 12,
    }
