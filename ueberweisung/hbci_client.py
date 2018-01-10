#!/usr/bin/env python3
import getpass
import logging
from pprint import pformat

from fints.client import FinTS3PinTanClient
import config
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO)
logging.getLogger("fints.dialog").setLevel(logging.WARN)

if __name__ == "__main__":

    pin = getpass.getpass("Please enter PIN: ")

    f = FinTS3PinTanClient(
        config.blz,
        config.user,
        pin,
        config.fints_url
    )

    accounts = f.get_sepa_accounts()
    logging.info(pformat(accounts))

    statement = f.get_statement(accounts[0], date.today() - timedelta(days=30), date.today())

    for transaction in statement:
        logging.info(pformat(transaction))
        logging.info(pformat(transaction.data))
