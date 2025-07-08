import datetime
from pprint import pformat

from money_utils import hbci_client


def test_hbci():
    with hbci_client.get_account() as (conn, acc):
        days = 30
        transactions = conn.get_transactions(
            acc, datetime.date.today() - datetime.timedelta(days=days), datetime.date.today()
        )
        print(f"got {len(transactions)} transactions for the last {days}")

