#!/usr/bin/env python3
import getpass
import logging
import subprocess
import sys
from datetime import date, timedelta
from pprint import pformat

from fints.client import *

import config

logging.basicConfig(level=logging.INFO)
logging.getLogger("fints.dialog").setLevel(logging.INFO)

pin = None
conn = None
accounts = None

version = subprocess.check_output(["git", "describe", "--abbrev=5", "--always"]).decode('utf8').strip()
print("version:", version)

def get_connection():
    logging.getLogger('fints').setLevel(logging.INFO)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)
    logging.getLogger('mt940.tags').setLevel(logging.INFO)

    global pin, conn
    if conn:
        try:
            conn.get_sepa_accounts()
            return conn
        except:
            conn = None

    if not pin:
        pin = config.pin
    if not pin:
        pin = getpass.getpass("Please enter PIN: ")
    conn = FinTS3PinTanClient(
        bank_identifier=config.blz,
        user_id=config.user,
        pin=pin,
        server=config.fints_url,
        product_id=config.product_id,
        mode=FinTSClientMode.INTERACTIVE,
        product_version=version
    )
    #conn.set_tan_mechanism('910')
    #conn.set_tan_mechanism('942')   # eg for mobiletan at gls

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
    statement = conn.get_transactions(account, date.today() - timedelta(days=30), date.today())

    for tx in statement:
        logging.info(pformat(tx.data))
        #logging.info("%s %s %s", tx.data['entry_date'], pformat(tx.data['amount']), tx.data['purpose'])
