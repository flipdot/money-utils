#!/usr/bin/env python3
# coding: utf8

import logging
import sys
from datetime import date, timedelta
from sqlalchemy import or_

from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session

import db
import util
from schema.member import Member
from schema.transaction import Transaction

logging.basicConfig(level=logging.INFO, format="%(levelname) 7s %(message)s")

def main(args):
    if '--debug' in args:
        logging.getLogger('').setLevel(logging.DEBUG)

    db.init()

    with db.tx() as session:
        for member in session.query(Member)\
                .order_by(Member.last_name, Member.first_name):
            analyze_member(member, session)


def replace_umlauts(str):
    return str.lower()\
        .replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")\
        .replace("ß", "ss")


def txs_by_member(session: Session, member: Member) -> Query:
    name_like = "%"+member.first_name+"%"+member.last_name+"%"
    name_reverse = "%"+member.last_name+"%"+member.first_name

    or_items = [
        Transaction.applicant_name.ilike(name_like),
        Transaction.applicant_name.ilike(name_reverse),
        Transaction.purpose.ilike(name_like),
        Transaction.purpose.ilike(name_reverse)
    ]

    if replace_umlauts(member.name) != member.name.lower():
        first = replace_umlauts(member.first_name)
        last = replace_umlauts(member.last_name)

        name_like_umlaut = "%"+first+"%"+last+"%"
        name_reverse_umlaut = "%"+last+"%"+first
        or_items.extend([
            Transaction.applicant_name.ilike(name_like_umlaut),
            Transaction.applicant_name.ilike(name_reverse_umlaut),
            Transaction.purpose.ilike(name_like_umlaut),
            Transaction.purpose.ilike(name_reverse_umlaut)
        ])

    return session.query(Transaction)\
        .filter(or_(Transaction.member_id.is_(None), Transaction.member_id == member.id))\
        .filter(or_(*or_items))\
        .filter(Transaction.purpose.notilike("%spende")) \
        .filter(Transaction.purpose.notilike("%spende %")) \
        .filter(Transaction.purpose.notilike("spende %")) \
        .filter(Transaction.purpose.notilike("spende")) \
        .filter(Transaction.purpose.notilike("drinks %")) \
        .filter(Transaction.amount > 0)\


def analyze_member(member, session):
    from_date = find_first_date(member, session)
    if not from_date:
        return
    today = date.today().replace(day=1)
    today = today.replace(month=today.month-1)
    logging.info("Member %s," % member.name +
        (" last amount %.2f" % member.last_fee if member.last_fee else ""))

    last_paid = None
    last_month_missing = False
    unchanged_months = 0
    for first_last in util.months(from_date, today):
        first_day, next_month = first_last
        month = first_day.strftime("%Y-%m")

        #logging.debug("  %s", first_day)
        txs: list[Transaction] = txs_by_member(session, member)\
            .filter(Transaction.date >= first_day)\
            .filter(Transaction.date < next_month)\
            .order_by(Transaction.date)

        month_sum = sum([tx.amount for tx in txs])

        for tx in txs:
            tx.member_id = member.id
            session.add(tx)

        if month_sum == 0:
            unchanged_months = 0
            if not last_month_missing:
                logging.warning("  No payment in %s" % first_day.strftime("%Y-%m"))
            last_month_missing = True
        elif member.last_fee is None or member.last_fee != month_sum:
            [logging.debug("    %s: % 20s | % .2f - %.50s",
                tx.date, tx.applicant_name, tx.amount, tx.purpose) for tx in txs]
            unchanged_months = 0

            logging.info("  %s - monthly amount%s EUR %.2f",
                month,
                " changed from %.2f to" % member.last_fee if member.last_fee else "",
                month_sum)
            if month_sum != 0:
                member.last_fee = month_sum
                session.add(member)
        else:
            unchanged_months += 1

        if month_sum > 0:
            last_month_missing = False
            last_paid = txs[-1].date

    if last_paid and last_paid + timedelta(days=31) < today:
        logging.warning("  Last paid was %s, marking as exit", last_paid)
        member.exit_date = last_paid + timedelta(days=30)
        session.add(member)
    elif unchanged_months > 1:
        member.fee = member.last_fee
        session.add(member)


def find_first_date(member, session: Session):
    if member.entry_date:
        return member.entry_date
    first_tx: Transaction = txs_by_member(session, member)\
        .order_by(Transaction.date).first()
    if not first_tx:
        logging.error("  No transactions for %s", member.name)
        return None
    member.entry_date = first_tx.date
    session.add(member)
    return first_tx.date


if __name__ == "__main__":
    sys.exit(main(sys.argv))
