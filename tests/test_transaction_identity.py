"""Tests for the transaction identity (``gen_id``).

SEPA/HBCI transactions carry no stable unique id, so the importer hashes a
5-tuple (date, entry_date, IBAN/BIC, amount, purpose, ...) to deduplicate
re-fetched transactions. If the hash inputs drift, a payment gets imported
twice (double income) or twice under different ids that never match again.

``gen_id`` exists twice, in the SQLAlchemy importer (schema.transaction) and
the Django web app (report.models). The two implementations must stay in
sync: they read and write the same database file.
"""
import hashlib
from types import SimpleNamespace

from schema.transaction import Transaction as SqlaTransaction
from report.models import Transaction as DjeTransaction
from tests.helpers import fake_amount, fake_tx_data, make_tx


def test_id_is_sha256_hex():
    tx = SqlaTransaction(make_tx())
    assert len(tx.tx_id) == 64
    int(tx.tx_id, 16)


def test_same_content_same_id():
    a = SqlaTransaction(make_tx(purpose='Miete max', amount=fake_amount('10.00')))
    b = SqlaTransaction(make_tx(purpose='Miete max', amount=fake_amount('10.00')))
    assert a.tx_id == b.tx_id


def test_id_changes_with_content():
    base = make_tx()
    base_id = SqlaTransaction(base).tx_id
    for field, value in [
        ('purpose', 'Miete jemand anderes'),
        ('amount', fake_amount('10.01')),
        ('date', type(base.data['date'])(2024, 1, 16)),
        ('applicant_iban', 'DE11 1111 1111 1111 1111 11'),
    ]:
        tx = SqlaTransaction(make_tx(**{field: value}))
        assert tx.tx_id != base_id, field


def test_sender_name_is_not_part_of_the_id():
    # By design the dedup key is the SEPA 5-tuple (date, IBAN, amount, ...),
    # not the sender's name: the same person pays from the same IBAN, so the
    # name carries no information the IBAN doesn't already have. Pin this so
    # adding it later (which would split every historical payment into a new
    # id) is a conscious decision.
    a = SqlaTransaction(make_tx(applicant_name='Max Mustermann')).tx_id
    b = SqlaTransaction(make_tx(applicant_name='Anderer Sender')).tx_id
    assert a == b


def test_both_implementations_agree():
    """The SQLAlchemy and Django importers hash the same fields.

    If someone edits one gen_id and not the other, re-imported transactions
    get new ids and duplicate rows appear.
    """
    payloads = [
        fake_tx_data(),
        fake_tx_data(purpose='Miete 2024-01 - 2024-03', amount=fake_amount('36.00')),
        fake_tx_data(applicant_name=None, applicant_iban='DE99 9999 9999 9999 9999 99',
                     end_to_end_reference='E2E-123'),
    ]
    for data in payloads:
        fake = SimpleNamespace(data=data)
        assert SqlaTransaction(fake).tx_id == DjeTransaction.from_sepa(fake).gen_id(), \
            data.get('purpose')


def test_id_matches_documented_formula():
    # pin the exact input ordering so a "harmless" reorder is caught
    from types import SimpleNamespace
    tx = SqlaTransaction(make_tx())
    data = tx.data
    raw = "|".join([
        str(data['date']),
        str(data['entry_date']),
        str(data['applicant_bin']),
        str(data['applicant_iban']),
        str(data['amount'].amount),
        str(data['transaction_code']),
        str(data['bank_type_id']),
        str(data['status']),
        str(data['prima_nota']),
        str(data['purpose']),
    ])
    assert hashlib.sha256(raw.encode('UTF8')).hexdigest() == tx.tx_id
