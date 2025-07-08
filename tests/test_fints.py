import datetime
import logging
from decimal import Decimal

import pytest
from fints.client import FinTS3PinTanClient, NeedTANResponse, FinTSUnsupportedOperation
from fints.hhd.flicker import terminal_flicker_unix
from fints.utils import minimal_interactive_cli_bootstrap

from money_utils.utils import get_config
from money_utils.bank.utils import ask_for_tan as _ask_for_tan

logging.basicConfig(level=logging.INFO)

@pytest.mark.skip(reason="use tests/test_bank_utils.py or tests/test_hbci.py")
def test_fints():
    # example from https://github.com/raphaelm/python-fints/issues/178

    config = get_config()
    f = FinTS3PinTanClient(
        config["bank_identifier"],
        config["user_id"],
        config["pin"],
        config["server"],
        product_id=config["product_id"],
    )
    minimal_interactive_cli_bootstrap(f)

    def ask_for_tan(r):
        return _ask_for_tan(f, r)

    # Open the actual dialog
    with f:
        # Since PSD2, a TAN might be needed for dialog initialization. Let's check if there is one required
        if f.init_tan_response:
            ask_for_tan(f.init_tan_response)

        # Fetch accounts
        accounts = f.get_sepa_accounts()
        if isinstance(accounts, NeedTANResponse):
            accounts = ask_for_tan(accounts)
        if len(accounts) == 1:
            account = accounts[0]
        else:
            print("Multiple accounts available, choose one")
            for i, mm in enumerate(accounts):
                print(i, mm.iban)
            choice = input("Choice: ").strip()
            account = accounts[int(choice)]

        # Test pausing and resuming the dialog
        dialog_data = f.pause_dialog()

    client_data = f.deconstruct(including_private=True)

    f = FinTS3PinTanClient(
        config["bank_identifier"],
        config["user_id"],
        config["pin"],
        config["server"],
        product_id=config["product_id"],
        from_data=client_data,
    )
    with f.resume_dialog(dialog_data):
        while True:
            operations = [
                "End dialog",
                "Fetch transactions of the last 30 days",
                "Fetch transactions of the last 120 days",
                "Fetch transactions XML of the last 30 days",
                "Fetch transactions XML of the last 120 days",
                "Fetch information",
                "Fetch balance",
                "Fetch holdings",
                "Fetch scheduled debits",
                "Fetch status protocol",
                "Make a simple transfer",
            ]

            print("Choose an operation")
            for i, o in enumerate(operations):
                print(i, o)
            choice = int(input("Choice: ").strip())
            try:
                if choice == 0:
                    break
                elif choice == 1:
                    res = f.get_transactions(
                        account,
                        datetime.date.today() - datetime.timedelta(days=30),
                        datetime.date.today(),
                    )
                    while isinstance(res, NeedTANResponse):
                        res = ask_for_tan(res)
                    print("Found", len(res), "transactions")
                elif choice == 2:
                    res = f.get_transactions(
                        account,
                        datetime.date.today() - datetime.timedelta(days=120),
                        datetime.date.today(),
                    )
                    while isinstance(res, NeedTANResponse):
                        res = ask_for_tan(res)
                    print("Found", len(res), "transactions")
                elif choice == 3:
                    res = f.get_transactions_xml(
                        account,
                        datetime.date.today() - datetime.timedelta(days=30),
                        datetime.date.today(),
                    )
                    while isinstance(res, NeedTANResponse):
                        res = ask_for_tan(res)
                    print("Found", len(res[0]) + len(res[1]), "XML documents")
                elif choice == 4:
                    res = f.get_transactions_xml(
                        account,
                        datetime.date.today() - datetime.timedelta(days=120),
                        datetime.date.today(),
                    )
                    while isinstance(res, NeedTANResponse):
                        res = ask_for_tan(res)
                    print("Found", len(res[0]) + len(res[1]), "XML documents")
                elif choice == 5:
                    print(f.get_information())
                elif choice == 6:
                    res = f.get_balance(account)
                    while isinstance(res, NeedTANResponse):
                        res = ask_for_tan(res)
                    print(res)
                elif choice == 7:
                    res = f.get_holdings(account)
                    while isinstance(res, NeedTANResponse):
                        res = ask_for_tan(res)
                    print(res)
                elif choice == 8:
                    res = f.get_scheduled_debits(account)
                    while isinstance(res, NeedTANResponse):
                        res = ask_for_tan(res)
                    print(res)
                elif choice == 9:
                    res = f.get_status_protocol()
                    while isinstance(res, NeedTANResponse):
                        res = ask_for_tan(res)
                    print(res)
                elif choice == 10:
                    res = f.simple_sepa_transfer(
                        account=accounts[0],
                        iban=input("Target IBAN:"),
                        bic=input("Target BIC:"),
                        amount=Decimal(input("Amount:")),
                        recipient_name=input("Recipient name:"),
                        account_name=input("Your name:"),
                        reason=input("Reason:"),
                        endtoend_id="NOTPROVIDED",
                    )
    
                    if isinstance(res, NeedTANResponse):
                        ask_for_tan(res)
            except FinTSUnsupportedOperation as e:
                print("This operation is not supported by this bank:", e)

