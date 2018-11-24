#!/usr/bin/env python3
# coding: utf8

import logging
import sys
from datetime import date, timedelta, datetime
from sqlalchemy import or_, desc

from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session

import db
import hbci_client
import util
from drinks import load_interval_max
from schema.member import Member
from schema.status import Status, LAST_LOAD
from schema.transaction import Transaction

MAX_LOAD_DAYS = 6 * 30
LOAD_BACK_DAYS = 5

logging.basicConfig(level=logging.INFO, format="%(levelname) 7s %(message)s")

def main(args):
    if '--debug' in args:
        logging.getLogger('').setLevel(logging.DEBUG)

    db.get()

    get_transactions()


def get_transactions():
    with db.tx() as session:
        last_load: Status = session.query(Status).filter_by(
            key=LAST_LOAD).fetchone()
        if last_load:
            logging.info("Last load was at %s", last_load.value_dt)
            if last_load.value_dt + load_interval_max > datetime.utcnow():
                return _query_transactions(session)

        logging.info("Loading fresh transactions")
        load_transactions(session)
    return _query_transactions(session)

def _query_transactions(session):
    return session.query(Transaction)

def load_transactions(session):

    last_transaction: Transaction = _query_transactions(session)\
        .order_by(desc(Transaction.date))\
        .fetchone()

    utcnow = datetime.utcnow()
    now = utcnow.date()
    if last_transaction:
        fetch_from = last_transaction.date - timedelta(days=LOAD_BACK_DAYS)
    else:
        fetch_from = now - timedelta(days = 365*2)

    while True:
        fetch_to = fetch_from + timedelta(days = MAX_LOAD_DAYS)
        if fetch_to > now:
            fetch_to = now

        load_chunk(session, fetch_from, fetch_to)

        if fetch_to >= now:
         break

    session.add(Status(key=LAST_LOAD, value_dt=utcnow))


def load_chunk(session: Session, fetch_from: datetime, fetch_to: datetime):
    acc = hbci_client.get_account()
    conn = hbci_client.get_connection()
    txs = conn.get_statement(acc, fetch_from, fetch_to)

    new_txs = [Transaction(tx) for tx in txs]
    logging.info("Fetched %d new txs", len(new_txs))
    session.add_all(new_txs)