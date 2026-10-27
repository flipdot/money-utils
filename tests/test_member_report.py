"""Tests for the ASCII member fee report (what the club actually reads)."""
import uuid
from datetime import date
from decimal import Decimal
from io import StringIO

from sqlalchemy import select

import member_report
from schema.fee_entry import FeeEntry
from schema.fee_util import PayInterval
from schema.member import Member
from schema.transaction import Transaction, TxType
from tests.helpers import fake_amount, make_tx


def add_fee_entry(session, member, month, fee):
    tx = Transaction(make_tx(date=month, entry_date=month,
                             amount=fake_amount(fee),
                             purpose='Miete max'))
    tx.tx_id = uuid.uuid4().hex
    tx.member_id = member.id
    tx.type = TxType.MEMBER_FEE
    session.add(tx)
    # like the production code, the entry is created with member_id; note
    # the (member, month) uniqueness constraint means at most one entry per
    # member and month, so the report's entry-count suffix can never trigger
    entry = FeeEntry(member_id=member.id, month=month, tx=tx,
                     fee=Decimal(fee), pay_interval=PayInterval.MONTHLY)
    session.add(entry)
    return entry


def render(session, member):
    buf = StringIO()
    member_report.members_table(
        session,
        session.scalars(select(Member).order_by(Member.last_name,
                                                Member.first_name)),
        date(2024, 1, 1), date(2024, 3, 1), to=buf)
    lines = buf.getvalue().splitlines()
    return lines[0], [l for l in lines if 'Mustermann' in l][0]


def test_members_table_shows_fees_per_month(session):
    member = Member(first_name='Max', last_name='Mustermann', nick='max')
    session.add(member)
    session.flush()
    # paid January and February, nothing in March
    add_fee_entry(session, member, date(2024, 1, 1), '10.00')
    add_fee_entry(session, member, date(2024, 2, 1), '23.00')
    session.flush()

    header, line = render(session, member)
    # header carries the month numbers
    assert ' 1  ' in header and ' 2  ' in header and ' 3  ' in header
    # per-month cells are ' {:>2.0f}{:1} '; note the (empty) count field is
    # a width-1 field, so it still renders as one space
    assert line.endswith(' 10   23       ')


def test_members_table_marks_missing_month(session):
    member = Member(first_name='Max', last_name='Mustermann', nick='max')
    session.add(member)
    session.flush()
    add_fee_entry(session, member, date(2024, 1, 1), '10.00')
    session.flush()

    _, line = render(session, member)
    assert line.endswith(' 10            ')
