#!/usr/bin/env python3

import logging
import sys
from contextlib import contextmanager
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import sessionmaker

import db as database
import cache
from member import Member, Base
from transaction import Transaction
from sqlalchemy.orm.session import Session
logging.basicConfig(level=logging.INFO)

def main(args):
    if '--debug' in args:
        logging.getLogger('').setLevel(logging.DEBUG)

    db = database.get()
    txs = database.table(database.table_tx)
    engine = db.engine
    maker = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    logging.info("example tx: %s", txs.find_one())

    with session_scope(maker) as session:
        for member in session.query(Member).order_by(Member.id):
            analyze_member(member, txs, db)

def analyze_member(member, tx_table, db):
    first_tx = tx_table.find_one(applicant_name=member.name, order_by='date')
    from_date: date = first_tx['date']
    today = date.today()
    logging.info("Member %s", member.name)
    last_amount = None

    for first_last in months(from_date, today):
        first_day, next_month = first_last
        month = first_day.strftime("%Y-%m")

        logging.debug("  %s", first_day)
        txs = db.query('SELECT * from `transaction` WHERE '
                       '(`applicant_name` LIKE :name OR `purpose` LIKE :name) '
                       'AND `date` >= :first AND `date` < :limit '
                       'ORDER BY `date`',
            name="%"+member.name+"%", first=first_day, limit=next_month)
        sum = 0
        texts = []
        for tx in txs:
            logging.debug("    %s: % 20s | % 5s - %s", tx['date'], tx['applicant_name'], tx['amount'], tx['purpose'])

            texts.append(tx['applicant_name']+ ": " + tx['purpose'])
            sum += tx['amount']

        if last_amount is None:
            logging.info("  Monthly amount: %s - EUR %s", month, sum)
            last_amount = sum
        elif last_amount != sum:
            logging.info("  Amount changed: %s - EUR %s", month, sum)
            last_amount = sum


def months(from_date, to_date):
    from_month = from_date.replace(day=1)
    to_month = to_date.replace(day=1)

    while from_month <= to_month:
        next = from_month + relativedelta(months=+1)
        yield from_month, next
        from_month = next

@contextmanager
def session_scope(Session: sessionmaker) -> Session:
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))