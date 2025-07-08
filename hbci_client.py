#!/usr/bin/env python3
import getpass
import subprocess
from datetime import date, timedelta
from pprint import pformat

from fints.client import *

import config
from fints.hhd.flicker import terminal_flicker_unix
import atexit

from client import save_client, client_from_config

logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
logging.getLogger("fints.dialog").setLevel(logging.DEBUG)

pin = None
conn = None
accounts = None

version = subprocess.check_output(["git", "describe", "--abbrev=5", "--always"]).decode('utf8').strip()
version = version[:5]

def terminal_tan_callback(response):
    logging.warning("Need TAN for transactions: %s", response.challenge)
    if getattr(response, 'challenge_hhduc', None):
        try:
            terminal_flicker_unix(response.challenge_hhduc)
        except KeyboardInterrupt as e:
            logging.exception("interrupt", e)
            pass
    while True:
        tan = input('Please enter TAN:')
        if tan:
            return tan

def get_connection(ask_for_tan=terminal_tan_callback):
    logging.getLogger('fints').setLevel(logging.INFO)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)
    logging.getLogger('mt940.tags').setLevel(logging.INFO)

    global pin, conn
    if conn:
        try:
            return conn
        except Exception as e:
            conn = None
            raise e

    if not pin:
        pin = config.pin
    if not pin:
        pin = getpass.getpass("Please enter PIN: ")

    conn = client_from_config()

    logging.info("registering shutdown hook")
    atexit.register(save_conn)
    return conn
    
def save_conn():
    global conn
    save_client(conn)
    # if conn:
    #     logging.info("registering atexit hook")
    #     data = conn.deconstruct(True)
    #     if not os.path.exists("data"):
    #         os.makedirs("data")
    #     with open("data/fints_state.bin", "wb") as fd:
    #         fd.write(data)

@contextmanager
def get_account(ask_for_tan=None):
    if not ask_for_tan:
        ask_for_tan = terminal_tan_callback
    conn = get_connection(ask_for_tan)
    with conn:
        global accounts
        if not accounts:
            accounts = conn.get_sepa_accounts()
        if isinstance(accounts, NeedTANResponse):
            logging.info("Calling tan callback for get_accounts %s", accounts)
            tan = ask_for_tan(accounts)
            accounts = conn.send_tan(accounts, tan)
        for acc in accounts:
            if acc.iban == config.iban:
                logging.info("Got account %s.", pformat(acc))
                yield conn, acc
                return
        raise Exception("IBAN %s not found (got %s)" % config.iban, pformat(accounts))

if __name__ == "__main__":
    account = get_account()
    statement = conn.get_transactions(account, date.today() - timedelta(days=30), date.today())

    for tx in statement:
        logging.info(pformat(tx.data))
        #logging.info("%s %s %s", tx.data['entry_date'], pformat(tx.data['amount']), tx.data['purpose'])
