#!/usr/bin/env python3
import getpass
import subprocess
from datetime import date, timedelta
from io import BytesIO
from pprint import pformat

from fints.client import *

import config
from fints.hhd.flicker import terminal_flicker_unix
import atexit

from client import save_client, client_from_config

from PIL import Image


logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
logging.getLogger("fints.dialog").setLevel(logging.DEBUG)

pin = None
conn = None
accounts = None

version = subprocess.check_output(["git", "describe", "--abbrev=5", "--always"]).decode('utf8').strip()
version = version[:5]


def encoded_png_to_unicode_qr(encoded_png, scaling_factor=1.0):
    image = Image.open(BytesIO(encoded_png))
    new_size = (int(image.width * scaling_factor), int(image.height * scaling_factor))
    image = image.resize(new_size, Image.LANCZOS)
    image = image.convert("L")

    empty_empty = " "
    empty_full = "▄"
    full_empty = "▀"
    full_full = "█"
    char_matrix = [[empty_empty, empty_full], [full_empty, full_full]]

    def pixel_to_code(pixel):
        return int(pixel / 255)

    unicode_str = ""
    for y in range(0, image.height, 2):
        for x in range(image.width):
            up = pixel_to_code(image.getpixel((x, y)))
            if y == image.height - 1:
                down = 0
            else:
                down = pixel_to_code(image.getpixel((x, y + 1)))
            unicode_char = char_matrix[up][down]
            unicode_str += unicode_char
        unicode_str += "\n"
    return unicode_str


def challenge_matrix_to_unicode_qr(challenge_matrix, scaling_factor=0.5):
    mime_type, encoded_png = challenge_matrix
    if mime_type == "image/png":
        return encoded_png_to_unicode_qr(encoded_png, scaling_factor)
    raise NotImplementedError(mime_type)

def terminal_tan_callback(response):
    logging.warning("Need TAN for transactions: %s", response.challenge)
    if getattr(response, 'challenge_hhduc', None):
        try:
            terminal_flicker_unix(response.challenge_hhduc)
        except KeyboardInterrupt as e:
            logging.exception("interrupt", e)
            pass
    elif getattr(response, "challenge_matrix", None):
        logging.info("Scan this qr code")
        logging.info("\n" + challenge_matrix_to_unicode_qr(response.challenge_matrix))
    while True:
        tan = input('Please enter TAN:')
        if tan:
            return tan

def get_connection(ask_for_tan=None):
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

    # TODO: ask_for_tan needs to be passed through, so that it
    #       also works in the web interface.
    #       However, currently it seems that we cannot pass the challenge in the Django UI.
    #       This will be tackled in a separate PR – for now, you are required to do the challenge on the
    #       command line.
    # conn = client_from_config(ask_for_tan)
    conn = client_from_config()

    logging.info("registering shutdown hook")
    atexit.register(save_conn)
    return conn
    
def save_conn():
    global conn
    save_client(conn)

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
