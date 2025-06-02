#!/bin/sh
"exec" "uv" "run" "$0" "$@"
# coding: utf8

import logging
import re
import sys
from collections import defaultdict, Counter
from datetime import date, timedelta
from typing import Dict, List, Tuple

from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, rrule
from fuzzywuzzy import fuzz
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session

import config
import db
import util
from schema.fee_entry import FeeEntry
from schema.fee_util import DetectMethod, PayInterval, common_fee_amounts, fee_amounts, month_regex_ym, month_regex_ymd, \
    month_regex_ymd_range
from schema.member import Member
from schema.transaction import Transaction, TxType

logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO,
    format="%(levelname) 7s %(message)s")

def main(args):
    if '--debug' in args:
        logging.getLogger('').setLevel(logging.DEBUG)

    db.init()
    logging.info("Analyzing Member fees...")

    with db.tx() as session:
        members = session.query(Member) \
            .order_by(Member.last_name, Member.first_name)
        link_transactions(session, members)

    # only use the current month if we are  past the 18th, instead use the last
    today = date.today() - timedelta(days=25)
    today = today.replace(day=1)
    logging.info("Analyzing until %s", today)

    with db.tx() as session:
        member_ids = session.query(Member.id) \
            .order_by(Member.last_name, Member.first_name)\
            .all()
    for id in member_ids:
        with db.tx() as session:
            analyze_member(session.query(Member).get(id), today, session)

    logging.info("Analyzing finished.")
    #TODO check whether tx entries in fee_entry match up with fee sum

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
        .filter(Transaction.purpose.notilike("%Getraenke")) \
        .filter(Transaction.purpose.notilike("%Einkauf%")) \
        .filter(Transaction.purpose.notilike("Baegeldeinzahlung%")) \
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

    logging.info(" === Member %d %s," % (member.id, member.name) +
        (" last amount %.2f" % member.last_fee if member.last_fee else "") +
        (" interval %s" % member.pay_interval.value if member.pay_interval else ""))

    all_txs = session.query(Transaction)\
        .filter(Transaction.member_id == member.id) \
        .filter(Transaction.type == TxType.MEMBER_FEE)\
        .order_by(Transaction.date)

    analyze_fees(member=member, today=today, session=session, all_txs=all_txs)

    last_paid = None
    last_month_missing = False
    unchanged_months = 0
    for first_day, next_month in util.months(from_date, today):
        month = first_day.strftime("%Y-%m")

        txs = session.query(Transaction)\
            .join(FeeEntry, Transaction.tx_id == FeeEntry.tx_id)\
            .filter(Transaction.member == member)\
            .filter(FeeEntry.month == first_day)\
            .all()

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


def analyze_fees(member, today, session: Session, all_txs: Query):
    txs_without_entry: List[Transaction] = all_txs \
        .outerjoin(FeeEntry, FeeEntry.tx_id == Transaction.tx_id) \
        .filter(FeeEntry.member_id.is_(None))\
        .all()
    logging.info("    Creating fee entries for %d new txs", len(txs_without_entry))

    for tx in txs_without_entry:
        logging.debug("tx w/o entry: %s", tx)
        entries = split_into_entries(member, session, tx)
        try:
            session.add_all(entries)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            logging.warning("Entries colliding! %s:", entries)
            logging.info("  Why: %s", e)
            delete_entries = session.query(FeeEntry).filter_by(member_id=member.id)\
                .filter(FeeEntry.month.in_([entry.month for entry in entries]))
            logging.warning("Deleting these: %s", delete_entries.all())
            delete_entries.delete(synchronize_session='fetch')


def split_into_entries(member, session, tx):
    month = tx.date + relativedelta(days=config.crossover_days)
    month = month.replace(day=1)
    entry = FeeEntry(member_id=member.id, month=month, tx=tx, fee=tx.amount,
        pay_interval=PayInterval.MONTHLY)
    
    months = month_command(tx)
    if months:
        entry.detect_method = DetectMethod.FEE_COMMAND
        return list(split_fee_command(tx, session, entry, months))
    elif tx.amount in fee_amounts:
        entry.detect_method = DetectMethod.LAST_FEE
        logging.info('fee entry amount: %s %s', entry.month, tx)
        return [entry]
    elif tx.amount / 12 == member.fee:
        entry.detect_method = DetectMethod.MULTIPLE_OF_FEE
        return list(split_fee_months(entry, session, 12, PayInterval.YEARLY, tx))
    elif tx.amount / 6 == member.fee:
        entry.detect_method = DetectMethod.MULTIPLE_OF_FEE
        return list(split_fee_months(entry, session, 6, PayInterval.SIX_MONTH, tx))
        
    elif tx.amount / 12 in common_fee_amounts:
        entry.detect_method = DetectMethod.MULTIPLE_OF_COMMON_FEE
        return list(split_fee_months(entry, session, 12, PayInterval.YEARLY, tx))
    elif tx.amount / 6 in common_fee_amounts:
        entry.detect_method = DetectMethod.MULTIPLE_OF_COMMON_FEE
        return list(split_fee_months(entry, session, 6, PayInterval.SIX_MONTH, tx))
    else:
        entry.detect_method = DetectMethod.FALLBACK
        logging.warning("Fee entry unclear! Assuming monthly for now")
        logging.info('fee entry unclear: %s %s', entry.month, tx)
        return [entry]


def split_fee_months(entry, session, num_months, pay_interval, tx):
    entry.fee /= num_months
    entry.pay_interval = pay_interval
    for m in range(num_months):
        month_replaced = entry.month + relativedelta(months=m)
        month_replaced = month_replaced.replace(day=1)
        m_entry = entry.replace(month=month_replaced)
        logging.info('fee entry split_fee_months: %s (%.2f) %s', m_entry.month, m_entry.fee, tx)
        yield m_entry


def month_command(tx):
    try:
        months = list(month_command_ymd(tx.purpose))
        if not months:
            return None
        for d in months:
            if d > tx.date + relativedelta(years=2) or d < tx.date - relativedelta(years=1):
                logging.warning("possible month command ignored, out of range (-2 years or +1 months): %s", tx)
                return None
        return months
    except (ValueError, KeyError):
        return None


def month_command_ymd(text):
    matches = list(month_regex_ymd_range.finditer(text))
    if matches:
        for match in matches:
            start = date(int(match.group('year_start')), int(match.group('month_start')), 1)
            end = date(int(match.group('year_end')), int(match.group('month_end')), 1)
            for d in rrule(MONTHLY, dtstart=start, until=end):
                yield d.date()
        return
    
    matches = list(month_regex_ymd.finditer(text))
    if matches:
        for match in matches:
            yield date(int(match.group('year')), int(match.group('month')), 1)
        return

    matches = list(month_regex_ym.finditer(text))
    if matches:
        for match in matches:
            yield date(2000 + int(match.group('year')), int(match.group('month')), 1)
        return
    month_names_or = "|".join(util.months_german.keys())
    matches = list(re.finditer(r'(?:^|\s)(?P<month>%s) ?(?P<year>\d{4})(?=$|\s)' % month_names_or, text))
    if matches:
        for match in matches:
            month_num = util.months_german[match.group('month')]
            yield date(int(match.group('year')), month_num, 1)
        return



def split_fee_command(tx, session, entry, months):
    logging.info("Tx matched fee commands for months %s", months)
    entry.fee /= len(months)
    entry.pay_interval = PayInterval.VARIABLE
    for month in months:
        m_entry = entry.replace(month=month)
        logging.info('fee entry split_fee_command: %s %s', m_entry, tx)
        yield m_entry


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
