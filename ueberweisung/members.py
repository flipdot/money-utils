#!/usr/bin/env python3
# coding: utf8

import logging
import re
import sys
from collections import defaultdict, Counter
from datetime import date, timedelta
from typing import Dict, List, Tuple

from fuzzywuzzy import fuzz
from sqlalchemy import or_, and_
from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session

import config
import db
import util
from schema.member import Member
from schema.transaction import Transaction, TxType

logging.basicConfig(level=logging.INFO, format="%(levelname) 7s %(message)s")

def main(args):
    if '--debug' in args:
        logging.getLogger('').setLevel(logging.DEBUG)

    db.init()

    with db.tx() as session:
        members = session.query(Member) \
            .order_by(Member.last_name, Member.first_name)
        link_transactions(session, members)

    # only use the current month if we are  past the 18th, instead use the last
    today = date.today() - timedelta(days=18)
    today = today.replace(day=1)
    logging.info("Analyzing until %s", today)

    with db.tx() as session:
        members = session.query(Member) \
            .order_by(Member.last_name, Member.first_name)
        for member in members:
            analyze_member(member, today, session)


def replace_umlauts_1(str):
    return str.lower()\
        .replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")\
        .replace("ß", "ss")

def replace_umlauts_2(str):
    return str.lower() \
        .replace("ä", "a").replace("ö", "o").replace("ü", "u") \
        .replace("ß", "s")


def like_name_patterns(member, glob="%"):
    if member.nick:
        yield glob + member.nick + glob
    yield glob + member.first_name + glob + member.last_name + glob
    yield glob + member.last_name + glob + member.first_name + glob
    if replace_umlauts_1(member.name) != member.name.lower():
        first = replace_umlauts_1(member.first_name)
        last = replace_umlauts_1(member.last_name)
        yield glob + first + glob + last + glob
        yield glob + last + glob + first + glob
    if replace_umlauts_2(member.name) != member.name.lower():
        first = replace_umlauts_2(member.first_name)
        last = replace_umlauts_2(member.last_name)
        yield glob + first + glob + last + glob
        yield glob + last + glob + first + glob


def txs_by_member(session: Session, member: Member) -> Query:
    or_items = [
        Transaction.applicant_name.ilike(p) for p in like_name_patterns(member)
    ] + [
        Transaction.purpose.ilike(p) for p in like_name_patterns(member)
    ]

    return session.query(Transaction)\
        .filter(or_(*or_items))\
        .filter(Transaction.purpose.notilike("%spende")) \
        .filter(Transaction.purpose.notilike("%spende %")) \
        .filter(Transaction.purpose.notilike("spende %")) \
        .filter(Transaction.purpose.notilike("spende")) \
        .filter(Transaction.purpose.notilike("drinks %")) \
        .filter(or_(Transaction.type == TxType.MEMBER_FEE, Transaction.type.is_(None)))\
        .filter(Transaction.amount > 0)


def choose_member(tx: Transaction, members: List[Member]):
    tx_tokens = " ".join([tx.purpose, tx.applicant_name])

    scores = Counter()
    for member in members:
        member_tokens = " ".join([member.first_name, member.last_name, member.nick])
        # purpose counts double
        score = fuzz.token_set_ratio(member_tokens, tx_tokens) +\
            fuzz.token_set_ratio(member_tokens, tx.purpose)
        scores[member] = score

    choice: Tuple[Member, int] = scores.most_common(1)[0]
    selected = choice[0]
    logging.info("  %s matches:", tx)
    for member, count in scores.items():
        logging.info("%s%d %s", " -->" if selected == member else "    ", count, member)

    return selected


def detect_fee_commands(tx):
    matches = re.findall(r'(?:^|\s)(2\d{3}-[01]\d)(?=$|\s)', tx.purpose)
    if matches:
        logging.info("Tx matched fee commands for months %s", matches)
        logging.info("  %s", tx)
        tx.fee_months = matches


def link_transactions(session, members):
    logging.info("Linking new transactions...")
    member_tx_set = defaultdict(set)
    tx_map: Dict[str, Transaction] = {}

    for member in members:
        member_txs: List[Transaction] = txs_by_member(session, member)\
            .filter(Transaction.member_id.is_(None)).all()
        for tx in member_txs:
            member_tx_set[tx.tx_id].add(member)
        tx_map.update({tx.tx_id: tx for tx in member_txs})

    for tx_id, members in member_tx_set.items():
        tx = tx_map[tx_id]
        if len(members) == 1:
            tx.member_id = next(iter(members)).id
        else:
            member = choose_member(tx, members)
            tx.member_id = member.id

        tx.type = TxType.MEMBER_FEE
        detect_fee_commands(tx)
        session.add(tx)

    logging.info("%d new links", len(member_tx_set))


def member_txs_additional(session, member, txs: List[Transaction]):
    """Detect some types of project expenses"""
    fee_txs = list(filter(lambda t: t.amount == member.last_fee, txs))
    nonfee_txs = list(filter(lambda t: t not in fee_txs, txs))
    if len(fee_txs) == 1 and len(nonfee_txs) > 0:
        for tx in nonfee_txs:
            logging.info("Marking as project expense: %s", tx)
            tx.type = TxType.PROJECT_EXPENSE
        session.add_all(nonfee_txs)
        return True
    return False


def analyze_member(member, today, session):
    from_date = find_first_date(member, session)
    if not from_date:
        return

    logging.info("member %d %s," % (member.id, member.name) +
        (" last amount %.2f" % member.last_fee if member.last_fee else ""))

    all_txs = session.query(Transaction)\
        .filter(Transaction.member_id == member.id) \
        .filter(Transaction.type == TxType.MEMBER_FEE)\
        .order_by(Transaction.date)

    last_paid = None
    last_month_missing = False
    unchanged_months = 0
    for first_day, next_month in util.months(from_date, today):
        month = first_day.strftime("%Y-%m")

        first_day -= timedelta(days=config.crossover_days)
        next_month -= timedelta(days=config.crossover_days)

        txs = all_txs\
            .filter(
                or_(
                    and_(
                        Transaction.fee_months.is_(None),
                        Transaction.date >= first_day,
                        Transaction.date < next_month
                    ),
                    Transaction.fee_months.contains(month)
                )
            ).all()

        month_sum = sum([tx.amount for tx in txs])

        if month_sum == 0:
            unchanged_months = 0
            if not last_month_missing:
                logging.warning("  No payment in %s" % first_day.strftime("%Y-%m"))
            last_month_missing = True
        else:
            if last_month_missing:
                logging.warning("  until %s" % first_day.strftime("%Y-%m"))
            last_month_missing = False

            if member.last_fee != month_sum and not member_txs_additional(session, member, txs):
                unchanged_months = 0
                fee_changed(session, member, month_sum, month, txs)
            else:
                unchanged_months += 1

        if month_sum > 0:
            last_month_missing = False
            last_paid = txs[-1].date

    if last_month_missing:
        logging.warning("  until now")

    if last_paid and last_paid + timedelta(days=31) < today:
        logging.warning("  Last paid was %s, marking as exit", last_paid)
        member.exit_date = last_paid + timedelta(days=30)
        session.add(member)
    elif unchanged_months > 1:
        member.fee = member.last_fee
        session.add(member)


def fee_changed(session, member, month_sum, month, txs):
    logging.info("  %s - monthly amount%s EUR %.2f",
                 month,
                 " changed from %.2f to" % member.last_fee if member.last_fee else "",
                 month_sum)
    if len(txs) > 1:
        for tx in txs:
            logging.info("    %s", tx)
    if month_sum != 0:
        member.last_fee = month_sum
        session.add(member)


def find_first_date(member, session: Session):
    if member.entry_date:
        return member.entry_date
    first_tx: Transaction = session.query(Transaction)\
        .filter(Transaction.member_id == member.id)\
        .order_by(Transaction.date).first()
    if not first_tx:
        logging.error("  No transactions for %s", member.name)
        return None
    member.entry_date = first_tx.date
    session.add(member)
    return first_tx.date


if __name__ == "__main__":
    sys.exit(main(sys.argv))
