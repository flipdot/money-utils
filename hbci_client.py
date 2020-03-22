#!/usr/bin/env python3
import getpass
import subprocess
from datetime import date, timedelta
from pprint import pformat

from fints.client import *
from fints.utils import minimal_interactive_cli_bootstrap

import config

logging.basicConfig(level=logging.INFO)
logging.getLogger("fints.dialog").setLevel(logging.DEBUG)

pin = None
conn = None
accounts = None

version = subprocess.check_output(["git", "describe", "--abbrev=5", "--always"]).decode('utf8').strip()
version = version[:5]


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
        #mode=FinTSClientMode.INTERACTIVE,
        product_version=version
    )
    conn.fetch_tan_mechanisms()
    conn.set_tan_mechanism('910')
    #minimal_interactive_cli_bootstrap(conn)
    #conn._need_twostep_tan_for_segment = lambda _: True

    return conn

@contextmanager
#TODO https://python-fints.readthedocs.io/en/latest/trouble.html
def get_account(tan_callback):
    global accounts
    if not accounts:
        conn = get_connection()
        with conn:
            if conn.init_tan_response:
                tan_callback(conn, conn.init_tan_response)
            dialog_data = conn.pause_dialog()
        accounts = conn.get_sepa_accounts()
    for acc in accounts:
        if acc.iban == config.iban:
            logging.info("Got account %s.", pformat(acc))
            return conn, acc
    raise Exception("IBAN %s not found (got %s)", config.iban, pformat(accounts))

if __name__ == "__main__":
    account = get_account()
    statement = conn.get_transactions(account, date.today() - timedelta(days=30), date.today())

    for tx in statement:
        logging.info(pformat(tx.data))
        #logging.info("%s %s %s", tx.data['entry_date'], pformat(tx.data['amount']), tx.data['purpose'])
