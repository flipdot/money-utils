from _sha256 import sha256

from sqlalchemy import Column, String, Numeric, Date

import db


class Transaction(db.Base):
    __tablename__ = 'transaction'

    _tx_id = Column(String, primary_key=True)

    amount = Column(Numeric())
    original_amount = Column(Numeric())
    date = Column(Date())
    entry_date = Column(Date())
    purpose = Column(String(), nullable=False)

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
    FRST_ONE_OFF_RECC = Column(String())
    old_SEPA_CI = Column(String())
    old_SEPA_additional_position_reference = Column(String())
    settlement_tag = Column(String())
    debitor_identifier = Column(String())
    compensation_amount = Column(String())

    def __init__(self, hbci_tx):
        #TODO
        self.data = hbci_tx.data
        self.data['_tx_id'] = self.tx_id()
        self.data['amount'] = self.data['amount'].amount

    def tx_id(self):
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