"""Shared helpers: fakes for the python-fints transaction shape.

Both the SQLAlchemy importer (``schema.transaction.Transaction.__init__``)
and the Django importer (``report.models.Transaction.from_sepa``) consume a
``tx.data`` dict in the shape python-fints produces. The fakes below build
exactly that shape so tests exercise the real parsing/dedup code paths.
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace


def fake_amount(amount) -> SimpleNamespace:
    return SimpleNamespace(amount=Decimal(str(amount)), currency='EUR')


def fake_tx_data(**overrides) -> dict:
    """A transaction payload as python-fints hands it out.

    Every non-optional field from ``schema.transaction.copy_fields`` is
    present; optional fields are omitted unless overridden.
    """
    data = {
        'amount': fake_amount('10.00'),
        'date': date(2024, 1, 15),
        'entry_date': date(2024, 1, 15),
        'purpose': 'Miete max',
        'applicant_bin': 'TESTBIC',
        'applicant_name': 'Max Mustermann',
        'applicant_iban': 'DE00 0000 0000 0000 0000 00',
        'currency': 'EUR',
        'extra_details': '',
        'customer_reference': '',
        'bank_reference': '',
        'bank_type_id': '',
        'status': 'C',
        'funds_code': '',
        'transaction_code': '',
        'posting_text': '',
        'prima_nota': '',
        'return_debit_notes': '',
        'recipient_name': '',
        'additional_purpose': '',
    }
    data.update(overrides)
    return data


class FakeHBciTx:
    """Stand-in for a python-fints transaction: just a ``.data`` dict."""

    def __init__(self, data: dict):
        self.data = data


def make_tx(**overrides) -> FakeHBciTx:
    return FakeHBciTx(fake_tx_data(**overrides))
