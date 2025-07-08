#!/usr/bin/env python3
from datetime import date, timedelta
from pprint import pformat

from fints.client import *
from fints.utils import minimal_interactive_cli_bootstrap

import pickle

from fints.hhd.flicker import terminal_flicker_unix
import atexit
import os
import time


from .utils import get_config
from .bank.utils import ask_for_tan
from .bank.client import client_from_config, save_client_with_config


# logging.basicConfig(level=logging.DEBUG) # if config.debug else logging.INFO)
# logging.getLogger("fints.dialog").setLevel(logging.DEBUG)

config = get_config()

conn = None
accounts = None

# version = subprocess.check_output(["git", "describe", "--abbrev=5", "--always"]).decode('utf8').strip()
# version = version[:5]


def get_connection(tan_callback):
    global conn
    if conn:
        try:
            return conn
        except Exception as e:
            conn = None
            raise e

    conn = client_from_config(config, tan_callback=tan_callback)
    atexit.register(save_conn)
    return conn


def save_conn():
    global conn
    if conn:
        save_client_with_config(conn, config)


@contextmanager
def get_account(tan_callback=None):
    if tan_callback is None:
        tan_callback = ask_for_tan
    conn = get_connection(tan_callback)
    # logging.info("connection received")
    print("connection received")
    with conn:
        logging.info("entered conn")
        global accounts
        if not accounts:
            logging.info("get sepa accounts")
            accounts = conn.get_sepa_accounts()
        logging.info("got accounts (maybe with NeedTANResponse)")
        if isinstance(accounts, NeedTANResponse):
            logging.info("Calling tan callback for get_accounts %s", accounts)
            accounts = ask_for_tan(accounts)
        for acc in accounts:
            if acc.iban == config["iban"]:
                logging.info("Got account %s.", pformat(acc))
                yield conn, acc
                return
        raise Exception("IBAN %s not found (got %s)" % config["iban"], pformat(accounts))


if __name__ == "__main__":
    account = get_account()
    statement = conn.get_transactions(
        account, date.today() - timedelta(days=30), date.today()
    )

    for tx in statement:
        logging.info(pformat(tx.data))
        # logging.info("%s %s %s", tx.data['entry_date'], pformat(tx.data['amount']), tx.data['purpose'])
