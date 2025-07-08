import datetime

from fints.client import NeedTANResponse

from money_utils.bank.utils import ask_for_tan
from money_utils.utils import get_config
from money_utils.bank.client import client_from_config, save_client_with_config


def test_bank_utils():
    config = get_config()
    client = client_from_config(config)

    with client:
        accounts = client.get_sepa_accounts()
        for account in accounts:
            print(f"Getting transactions for account {account.iban}")
            result = client.get_transactions(
                account,
                start_date=datetime.datetime.now() - datetime.timedelta(days=1),
                end_date=datetime.datetime.now(),
            )
            if isinstance(result, NeedTANResponse):
                result = ask_for_tan(client, result)
            else:
                print("No TAN is required")
            print(f"Got {len(result)} transactions for {account.iban} since yesterday")

        save_client_with_config(client, config)

