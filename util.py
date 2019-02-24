from datetime import date
from typing import Iterable, Iterator

from dateutil.relativedelta import relativedelta


def months(from_date: date, to_date: date) -> Iterator[date]:
    from_month = from_date.replace(day=1)
    to_month = to_date.replace(day=1)

    while from_month <= to_month:
        next = from_month + relativedelta(months=+1)
        yield from_month, next
        from_month = next

months_german = {
    'Januar': 1,
    'Februar': 2,
    'Maerz': 3,
    'April': 4,
    'Mai': 5,
    'Juni': 6,
    'Juli': 7,
    'August': 8,
    'September': 9,
    'Oktober': 10,
    'November': 11,
    'Dezember': 12,
}
