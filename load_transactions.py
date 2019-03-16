#!/bin/sh
"exec" "`dirname $0`/.env/bin/python" "$0" "$@"
# coding: utf8

import logging
import sys
from datetime import date, timedelta, datetime
from sqlalchemy import or_, desc

from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session

import config
import db
import hbci_client
import util
from drinks import load_interval_max
from schema.member import Member
from schema.status import Status, LAST_LOAD
from schema.transaction import Transaction

MAX_LOAD_DAYS = 6 * 30
# grace time of days to fetch extra
LOAD_BACK_DAYS = 4

logging.basicConfig(level=logging.INFO, format="%(levelname) 7s %(module)s - %(message)s")

def main(args):
    if '--debug' in args:
        config.debug = True
    if config.debug:
        logging.getLogger('').setLevel(logging.DEBUG)
    db.init(config.debug)

    get_transactions(True)


def get_transactions(force=False):
    with db.tx() as session:
        last_load: Status = session.query(Status).filter_by(
            key=LAST_LOAD).first()
        if last_load:
            logging.info("Last load was at %s", last_load.value_dt)
            if not force and last_load.value_dt + load_interval_max > datetime.utcnow():
                logging.info("Quite recent, not loading new txs")
                return
        else:
            last_load = Status(key=LAST_LOAD)

        logging.info("Loading fresh transactions")
        load_transactions(session, last_load)

def _query_transactions(session):
    return session.query(Transaction)

def load_transactions(session, last_load: Status):

    last_transaction: Transaction = _query_transactions(session)\
        .order_by(desc(Transaction.entry_date))\
        .first()

    utcnow = datetime.utcnow()
    now = utcnow.date()
    if last_transaction:
        fetch_from = last_transaction.entry_date - timedelta(days=LOAD_BACK_DAYS)
    else:
        fetch_from = now - timedelta(days = 365*2)

    while True:
        fetch_to = fetch_from + timedelta(days = MAX_LOAD_DAYS)
        if fetch_to > now:
            fetch_to = now

        res = load_chunk(session, fetch_from, fetch_to, now)
        if not res:
            return
        if fetch_to >= now:
            break

    last_load.value_dt = utcnow
    session.add(last_load)


def load_chunk(session: Session, fetch_from: date, fetch_to: date, now: date):
    global error
    logging.info("Fetching TXs from %s to %s", fetch_from, fetch_to)
    acc = hbci_client.get_account()
    conn = hbci_client.get_connection()
    error = False
    def log_callback(_, response):
        if response.code[0] not in ('0', '1', '3'): # 0&1 info, 3 warning, rest err
            global error
            error = True

    conn.add_response_callback(log_callback)
    txs = conn.get_transactions(acc, fetch_from, fetch_to)

    new_txs = []
    for tx in txs:
        tx = Transaction(tx)
        if tx.entry_date > now:
            logging.warning("Ignoring future tx: %s", tx)
            continue
        fuzz = timedelta(days=config.import_fuzz_grace_days)
        if tx.date + fuzz < fetch_from or tx.date - fuzz > fetch_to:
            logging.warning("Ignoring tx which is not in requested range: %s", tx)
            continue
        new_txs.append(tx)

    logging.info("Fetched %d txs", len(new_txs))
    if error:
        logging.error("Errors occurred")
        session.rollback()
        return False

    for tx in new_txs:
        session.merge(tx)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
