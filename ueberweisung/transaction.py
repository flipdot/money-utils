from _sha256 import sha256
from datetime import date, datetime


class ImmutableException(BaseException):
    pass


class Transaction:
    data: dict = None
    id: str = None

    def __init__(self, hbci_tx):
        self.data = hbci_tx.data
        self.data['_tx_id'] = self.tx_id()
        self.data['amount'] = self.data['amount'].amount

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __setitem__(self, key, value):
        raise ImmutableException("Nope, nope, nope")

    def __iter__(self):
        return self.data.__iter__()

    def items(self):
        return self.data.items()

    def tx_id(self):
        # hash together as much as possible
        # there are NO unique transaction IDs in hbci...
        raw = "|".join([
            str(self.data['date']),
            str(self.data['entry_date']),
            str(self.data['applicant_bin']),
            str(self.data['applicant_iban']),
            str(self.data['amount']),
            str(self.data['transaction_code']),
            str(self.data['id']),
            str(self.data['status']),
            str(self.data['prima_nota']),
            str(self.data['purpose']),
        ])
        sha = sha256(raw.encode("UTF8"))
        return sha.hexdigest()