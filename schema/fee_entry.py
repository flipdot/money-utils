from sqlalchemy import Column, Integer, String, Numeric, Date, Enum, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship

from db import Base
from schema.fee_util import DetectMethod, PayInterval
from schema.transaction import Transaction


class FeeEntry(Base):
    __tablename__ = 'fee_entry'

    id = Column(String(), primary_key=True)
    pk = UniqueConstraint('member_id', 'month')

    member_id = Column(Integer(), ForeignKey('member.id'))
    month = Column(Date(), CheckConstraint("date(month, 'start of month') == month"), primary_key=True)

    tx_id = Column(String(), ForeignKey('transaction.tx_id'), nullable=False)
    fee = Column(Numeric(), nullable=False)
    pay_interval = Column(Enum(PayInterval), nullable=False,
        default=PayInterval.MONTHLY)

    detect_method = Column(Enum(DetectMethod), nullable=False,
        default=DetectMethod.FALLBACK)

    # --- Relationships ---

    member = relationship('Member', back_populates='fee_entries')
    tx = relationship(Transaction, back_populates='fee_entries')

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return "FeeEntry{x}".format(x=self.__dict__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = "{}|{}".format(self.member_id, self.month)

    def replace(self, **kwargs):
        for key in ['member_id', 'month', 'tx_id', 'fee', 'pay_interval']:
            if kwargs.get(key, None) is None:
                if key not in self.__dict__ and key == 'tx_id':
                    kwargs[key] = self.tx.tx_id
                else:
                    kwargs[key] = self.__dict__[key]
        return FeeEntry(**kwargs)

