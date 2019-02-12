#!/usr/bin/python3
import logging
import os
import pickle
import re
from datetime import timedelta, date, datetime
from hashlib import sha256
from pprint import pprint, pformat

from mt940.models import Date

import config
import hbci_client as hbci
from cache import load_cache, save_cache

load_back_initial = timedelta(days=365 * 1)
load_back_incremental = timedelta(days=7)
load_interval_max = timedelta(minutes=config.load_interval_minutes)

drinks_regex = re.compile(r'^drinks?\s+(?P<uid>\d+)(\s+(?P<info>.*))?$', re.I)
#drinks_regex = re.compile(r'^MIETE?\s+(?P<info>.*)\s+(?P<uid>\d+)$', re.I)


logging.basicConfig(level=logging.INFO)

def tx_id(tx):
    # hash together as much as possible
    # there are NO unique transaction IDs in hbci...
    raw = "|".join([
        str(tx.data['date']),
        str(tx.data['entry_date']),
        str(tx.data['applicant_bin']),
        str(tx.data['applicant_iban']),
        str(tx.data['amount']),
        str(tx.data['transaction_code']),
        str(tx.data['id']),
        str(tx.data['status']),
        str(tx.data['prima_nota']),
        str(tx.data['posting_text']),
        str(tx.data['purpose']),
    ])
    sha = sha256(raw.encode("UTF8"))
    return sha.hexdigest()

def load_txs():
    cache = load_cache()

    if 'last_load' in cache:
        logging.info("Last load was at %s", cache['last_load'])
        if cache['last_load'] + load_interval_max > datetime.utcnow():
            return cache['txs']

    last_tx_date = None
    for tx in cache['txs'].values():
        if not last_tx_date or tx.data['date'] > last_tx_date:
            last_tx_date = tx.data['date']

    logging.info("Latest tx cached from %s", last_tx_date)
    load_back = load_back_initial
    if last_tx_date and date.today() - last_tx_date < load_back_incremental:
        load_back = load_back_incremental
    now = date.today()
    back = now - load_back
    logging.info("Loading from %s to %s", back, now)
    acc = hbci.get_account()
    conn = hbci.get_connection()
    txs = conn.get_transactions(acc, back, now)
    new = 0
    shas_this = {}
    for tx in txs:
        sha = tx_id(tx)
        if sha not in cache['txs']:
            cache['txs'][sha] = tx
            new += 1
        if sha in shas_this:
            other = shas_this[sha]
            logging.warning("Duplicate SHA %s! \n old %s\n   vs\n new %s",
                            sha, pformat(other.data), pformat(tx.data))
        else:
            shas_this[sha] = tx
    logging.info("Fetched %d new txs. Got %d total.", new, len(cache['txs']))
    cache['last_load'] = datetime.utcnow()
    save_cache()
    return cache['txs']

def load_recharges():
    txs = load_txs()
    recharges_by_uid = {}
    for tx in txs.values():
        if type(tx.data['purpose']) != str:
            continue
        match = drinks_regex.match(tx.data['purpose'])
        if not match:
            continue
        if not tx.data['amount'].currency == "EUR":
            continue
        uid = match.group("uid")
        amount = tx.data['amount'].amount
        tx_date = str(tx.data['date'])
        if uid not in recharges_by_uid:
            recharges_by_uid[uid] = []
        info = match.group("info")
        info = re.sub(r'[^\w \-_.,;:]', '_', info) if info else ''
        r = {'uid': uid, 'info': info, 'amount': amount, 'date': tx_date}
        recharges_by_uid[uid].append(r)
    # sort all
    for uid in recharges_by_uid:
        recharges_by_uid[uid] = sorted(recharges_by_uid[uid], key=lambda r: r['date'])
    return recharges_by_uid

if __name__ == "__main__":
    charges = load_recharges()
    pprint(charges)

    txs = load_txs()
    txs = txs.values()
    txs = sorted(txs, key=lambda t: t.data['date'])
    #pprint([t.data for t in txs[10:]])
