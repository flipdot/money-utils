import logging
from _sha256 import sha256
from datetime import datetime

from sqlalchemy import Column, String, Numeric, Date, DateTime, Integer, ForeignKey

import config
from db import Base
from schema.member import Member

copy_fields = [
    'original_amount',
    'date',
    'entry_date',
    'purpose',
    'applicant_bin',
    'applicant_name',
    'applicant_iban',
    'currency',
    'extra_details',
    'customer_reference',
    'bank_reference',
    'id',
    'status',
    'funds_code',
    'transaction_code',
    'posting_text',
    'prima_nota',
    'return_debit_notes',
    'recipient_name',
    'additional_purpose',
    'gvc_applicant_iban',
    'gvc_applicant_bin',
    'end_to_end_reference',
    'additional_position_reference',
    'applicant_creditor_id',
    'purpose_code',
    'additional_position_date',
    'deviate_applicant',
    'deviate_recipient',
    'old_SEPA_CI',
    'old_SEPA_additional_position_reference',
    'settlement_tag',
    'debitor_identifier',
    'compensation_amount',
]

optional_fields = [
    'original_amount',
    'gvc_applicant_iban',
    'gvc_applicant_bin',
    'end_to_end_reference',
    'additional_position_reference',
    'additional_position_date',
    'applicant_creditor_id',
    'purpose_code',
    'deviate_applicant',
    'deviate_recipient',
    'old_SEPA_CI',
    'old_SEPA_additional_position_reference',
    'settlement_tag',
    'debitor_identifier',
    'compensation_amount',
]

empty_fields = [
    'purpose',
]

class Transaction(Base):
    __tablename__ = 'transaction'

    tx_id = Column(String, primary_key=True)

    member_id = Column(Integer, ForeignKey('member.id'), nullable=True)

    amount = Column(Numeric())
    original_amount = Column(Numeric())
    date = Column(Date())
    entry_date = Column(Date())
    purpose = Column(String(), nullable=False)

    import_date = Column(DateTime(), default=datetime.utcnow(), nullable=False)

    applicant_bin = Column(String()) # BIC
    applicant_name = Column(String())
    applicant_iban = Column(String())

    currency = Column(String())
    extra_details = Column(String())

    customer_reference = Column(String())
    bank_reference = Column(String())

    id = Column(String())
    status = Column(String()) # C
    funds_code = Column(String())
    transaction_code = Column(String())
    posting_text = Column(String())
    prima_nota = Column(String())
    return_debit_notes = Column(String())
    recipient_name = Column(String())
    additional_purpose = Column(String())
    gvc_applicant_iban = Column(String())
    gvc_applicant_bin = Column(String())
    end_to_end_reference = Column(String())
    additional_position_reference = Column(String())
    applicant_creditor_id = Column(String())
    purpose_code = Column(String())
    additional_position_date = Column(String())
    deviate_applicant = Column(String())
    deviate_recipient = Column(String())
    old_SEPA_CI = Column(String())
    old_SEPA_additional_position_reference = Column(String())
    settlement_tag = Column(String())
    debitor_identifier = Column(String())
    compensation_amount = Column(String())

    def __init__(self, hbci_tx):
        data = hbci_tx.data
        self.data = data
        self.amount = data['amount'].amount

        for key in copy_fields:
            if config.debug:
                if key not in data and key not in optional_fields:
                    logging.error("Putting key %s in optional fields list", key)
                    optional_fields.append(key)
            if key not in optional_fields:
                value = data[key]
            else:
                value = data[key] if key in data else None
            self.__dict__[key] = value

        for key in empty_fields:
            if self.__dict__[key] is None:
                self.__dict__[key] = ''

        self.tx_id = self.gen_id()

    def gen_id(self):
        # hash together as much as possible
        # there are NO unique transaction IDs in hbci...
        raw = "|".join([
            str(self.date),
            str(self.entry_date),
            str(self.applicant_bin),
            str(self.applicant_iban),
            str(self.amount),
            str(self.transaction_code),
            str(self.id),
            str(self.status),
            str(self.prima_nota),
            str(self.purpose),
        ])
        sha = sha256(raw.encode("UTF8"))
        return sha.hexdigest()

    def __str__(self) -> str:
        return "Tx[from: '{sender}', purpose: '{purpose}', amount: {amount:.2f}, date: {date}]"\
            .format(sender=self.applicant_name, purpose=self.purpose, amount=self.amount, date=self.date)

    def __repr__(self):
        return self.__str__()

