#!/usr/bin/env python3
import getpass
import logging
from datetime import date, timedelta
from pprint import pformat

from fints.client import FinTS3PinTanClient

import config

logging.basicConfig(level=logging.INFO)
logging.getLogger("fints.dialog").setLevel(logging.WARN)

pin = None
conn = None
accounts = None

def get_connection():
    global pin, conn
    if conn:
        try:
            conn.get_sepa_accounts()
            return conn
        except:
            conn = None

    if not pin:
        pin = getpass.getpass("Please enter PIN: ")
    conn = FinTS3PinTanClient(
        config.blz,
        config.user,
        pin,
        config.fints_url
    )
    return conn

def get_account():
    global accounts
    if not accounts:
        conn = get_connection()
        accounts = conn.get_sepa_accounts()
    for acc in accounts:
        if acc.iban == config.iban:
            logging.info("Got account %s.", pformat(acc))
            return acc
    raise Exception("IBAN %s not found (got %s)", config.iban, pformat(accounts))

if __name__ == "__main__":
    account = get_account()
    statement = conn.get_statement(account, date.today() - timedelta(days=30), date.today())

    for tx in statement:
        logging.info(pformat(tx.data))
        #logging.info("%s %s %s", tx.data['entry_date'], pformat(tx.data['amount']), tx.data['purpose'])
