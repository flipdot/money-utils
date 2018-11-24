from dateutil.relativedelta import relativedelta


def months(from_date, to_date):
    from_month = from_date.replace(day=1)
    to_month = to_date.replace(day=1)

    while from_month <= to_month:
        next = from_month + relativedelta(months=+1)
        yield from_month, next
        from_month = next

