"""End-to-end tests for the per-member fee analysis (``members.analyze_member``).

This is the code that turns raw bank transactions into the club's books:
which member paid for which month, fee changes, and whether a member has
quit. Tests run against the real SQLAlchemy models on in-memory SQLite.
"""
import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import func, select

import members
from members import (analyze_member, choose_member, like_name_patterns,
                     txs_by_member)
from schema.fee_entry import FeeEntry
from schema.fee_util import DetectMethod
from schema.member import Member
from schema.transaction import Transaction, TxType
from tests.helpers import fake_amount, make_tx


def make_member(session, first='Max', last='Mustermann', nick='max', **kwargs):
    member = Member(first_name=first, last_name=last, nick=nick, **kwargs)
    session.add(member)
    session.flush()
    return member


def add_fee_tx(session, member, tx_date, amount, purpose='Miete max',
               applicant='Max Mustermann'):
    tx = Transaction(make_tx(date=tx_date, entry_date=tx_date,
                             amount=fake_amount(amount), purpose=purpose,
                             applicant_name=applicant))
    # the generated tx_id is a hash of the content; make it unique so tests
    # can add several identical-looking transactions
    tx.tx_id = uuid.uuid4().hex
    tx.member_id = member.id
    tx.type = TxType.MEMBER_FEE
    session.add(tx)
    return tx


def fee_entry_months(session, member):
    rows = session.execute(
        select(FeeEntry.month, func.sum(FeeEntry.fee))
        .where(FeeEntry.member_id == member.id)
        .group_by(FeeEntry.month)).all()
    return {month: fee for month, fee in rows}


class TestAnalyzeMember:
    def test_steady_monthly_payer(self, session):
        member = make_member(session, entry_date=date(2024, 1, 1))
        add_fee_tx(session, member, date(2024, 1, 10), '10.00')
        add_fee_tx(session, member, date(2024, 2, 10), '10.00')
        add_fee_tx(session, member, date(2024, 3, 10), '10.00')
        session.flush()

        # analyze through March; every analyzed month is paid
        analyze_member(member, today=date(2024, 3, 1), session=session)
        session.commit()

        assert member.exit_date is None
        assert member.last_fee == Decimal('10.00')
        # fee is only set when the most recently analyzed month is paid too
        assert member.fee == Decimal('10.00')
        assert fee_entry_months(session, member) == {
            date(2024, 1, 1): Decimal('10.00'),
            date(2024, 2, 1): Decimal('10.00'),
            date(2024, 3, 1): Decimal('10.00'),
        }

    def test_fee_not_set_when_latest_month_missing(self, session):
        # an unpaid current month resets the unchanged counter, so the
        # member's fee is not (re)confirmed
        member = make_member(session, entry_date=date(2024, 1, 1))
        add_fee_tx(session, member, date(2024, 1, 10), '10.00')
        add_fee_tx(session, member, date(2024, 2, 10), '10.00')
        session.flush()

        analyze_member(member, today=date(2024, 3, 1), session=session)
        session.commit()

        assert member.fee is None
        assert member.last_fee == Decimal('10.00')

    def test_quitting_member_is_marked(self, session):
        # one payment in January, nothing since; "today" is May
        member = make_member(session, entry_date=date(2024, 1, 1))
        add_fee_tx(session, member, date(2024, 1, 10), '10.00')
        session.flush()

        analyze_member(member, today=date(2024, 5, 1), session=session)
        session.commit()

        assert member.exit_date == date(2024, 2, 9)  # last paid + 30 days

    def test_yearly_lump_sum_is_split(self, session):
        # 120.00 = 12 x 10.00 (common student fee)
        member = make_member(session, entry_date=date(2024, 1, 1))
        add_fee_tx(session, member, date(2024, 1, 5), '120.00',
                   purpose='Jahresbeitrag')
        session.flush()

        analyze_member(member, today=date(2024, 1, 1), session=session)
        session.commit()

        months = fee_entry_months(session, member)
        assert set(months) == {date(2024, m, 1) for m in range(1, 13)}
        assert all(fee == Decimal('10.00') for fee in months.values())
        # note: analyze_member's month sum uses the full transfer amount,
        # not the per-month fee entry share, so last_fee ends up as the
        # lump sum, not the monthly share
        assert member.last_fee == Decimal('120.00')
        assert member.exit_date is None

    def test_month_command_payment_is_split(self, session):
        member = make_member(session, entry_date=date(2024, 1, 1))
        add_fee_tx(session, member, date(2024, 1, 5), '20.00',
                   purpose='Miete 2024-01 - 2024-02')
        session.flush()

        analyze_member(member, today=date(2024, 3, 1), session=session)
        session.commit()

        entries = session.scalars(select(FeeEntry)
            .where(FeeEntry.member_id == member.id)).all()
        assert {e.month for e in entries} == {date(2024, 1, 1), date(2024, 2, 1)}
        assert all(e.fee == Decimal('10.00') for e in entries)
        assert all(e.detect_method == DetectMethod.FEE_COMMAND for e in entries)

    def test_payment_after_crossover_counts_for_next_month(self, session):
        # config.crossover_days = 10: a payment on the 29th is next month's
        member = make_member(session, entry_date=date(2024, 1, 1))
        add_fee_tx(session, member, date(2024, 1, 29), '23.00')
        session.flush()

        analyze_member(member, today=date(2024, 3, 1), session=session)
        session.commit()

        assert fee_entry_months(session, member) == {
            date(2024, 2, 1): Decimal('23.00')}
        assert member.last_fee == Decimal('23.00')

    def test_extra_payment_in_paid_month_is_project_expense(self, session):
        # member_txs_additional marks the non-fee transfer as project
        # expense so it does not count as a fee change. (In the normal
        # analysis flow a month can only ever contain one transaction's
        # entries because of the (member, month) uniqueness constraint, so
        # this logic only matters for data created out of band; it is
        # tested directly here.)
        member = SimpleNamespace(last_fee=Decimal('10.00'))
        fee_tx = Transaction(make_tx(amount=fake_amount('10.00')))
        expense_tx = Transaction(make_tx(amount=fake_amount('15.00'),
                                         purpose='Einkauf'))
        assert members.member_txs_additional(session, member,
                                             [fee_tx, expense_tx]) is True
        assert expense_tx.type == TxType.PROJECT_EXPENSE
        assert fee_tx.type is None

    def test_member_txs_additional_needs_exactly_one_fee_tx(self, session):
        member = SimpleNamespace(last_fee=Decimal('10.00'))
        txs = [Transaction(make_tx(amount=fake_amount('10.00'), purpose=p))
               for p in ('a', 'b')]
        # two fee-sized transfers: no project expense can be singled out
        assert members.member_txs_additional(session, member, txs) is False
        assert all(tx.type is None for tx in txs)

    def test_collision_drops_the_month_until_data_changes(self, session):
        """Documented behavior of the known collision bug (issue #110).

        Two transactions that resolve to the same month: the first is
        stored, the second collides on the (member, month) uniqueness
        constraint. The current code deletes the stored entry but never
        re-inserts the new one. Because both transactions remain
        unassigned, every subsequent run repeats the exact same sequence
        and the month stays empty -- the payment is missing from the
        report indefinitely (and eventually the member gets marked as
        having quit), until one of the transactions is corrected.
        """
        member = make_member(session, entry_date=date(2024, 1, 1))
        add_fee_tx(session, member, date(2024, 1, 5), '23.00')
        add_fee_tx(session, member, date(2024, 1, 6), '23.00')
        session.flush()

        analyze_member(member, today=date(2024, 1, 1), session=session)
        session.commit()
        assert fee_entry_months(session, member) == {}

        # a second run does not heal the data: the same collision recurs
        analyze_member(member, today=date(2024, 1, 1), session=session)
        session.commit()
        assert fee_entry_months(session, member) == {}


class TestNameMatching:
    def test_like_name_patterns_plain(self):
        member = Member(first_name='Max', last_name='Mustermann', nick='max')
        assert set(like_name_patterns(member)) == {
            '%max%', '%Max%Mustermann%', '%Mustermann%Max%'}

    def test_like_name_patterns_umlauts(self):
        member = Member(first_name='Jörg', last_name='Müller', nick='joe')
        assert set(like_name_patterns(member)) == {
            '%joe%',
            '%Jörg%Müller%', '%Müller%Jörg%',
            # ae/oe/ue/ss spellings
            '%joerg%mueller%', '%mueller%joerg%',
            # plain a/o/u/s spellings
            '%jorg%muller%', '%muller%jorg%'}

    def test_choose_member_picks_best_name_match(self):
        anna_berger = Member(first_name='Anna', last_name='Berger', nick='anna')
        anna_schmidt = Member(first_name='Anna', last_name='Schmidt', nick='schmidt')
        tx = SimpleNamespace(purpose='Miete anna', applicant_name='Anna Berger')
        assert choose_member(tx, [anna_berger, anna_schmidt]) is anna_berger

    def test_txs_by_member_excludes_non_fee_purposes(self, session):
        member = make_member(session)
        # (purpose, tx type, amount, expected to be linked as fee)
        cases = [
            ('Miete max', None, '10.00', True),
            ('Spende max', None, '10.00', False),        # donations are not fees
            ('spende für max', None, '10.00', False),
            ('xyz spende abc', None, '10.00', False),    # keyword in the middle
            ('drinks 123 max', None, '10.00', False),    # drink recharges
            ('drink 123 max', None, '10.00', False),     # singular form
            ('Getraenke max', None, '10.00', False),
            ('Einkauf getraenke max', None, '10.00', False),
            ('Baegeldeinzahlung max', None, '10.00', False),
            ('Miete max', TxType.PROJECT_EXPENSE, '10.00', False),
            ('Miete max', None, '-10.00', False),        # refunds
        ]
        txs = []
        for purpose, type_, amount, _ in cases:
            tx = add_fee_tx(session, member, date(2024, 1, 1), amount,
                            purpose=purpose)
            tx.member_id = None  # link_transactions operates on unlinked txs
            tx.type = type_
            txs.append(tx)
        session.flush()

        linked = session.scalars(
            txs_by_member(member).where(Transaction.member_id.is_(None))).all()
        assert [t.purpose for t in linked] == ['Miete max']
