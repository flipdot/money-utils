import enum

from sqlalchemy import Column, Integer, String, Numeric, Date, Enum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

from db import Base

class PayInterval(enum.Enum):
    MONTHLY = 1
    SIX_MONTH = 2
    YEAR = 3
    VARIABLE = 4

class Member(Base):
    __tablename__ = 'member'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(), nullable=False, default='')
    last_name = Column(String(), nullable=False, default='')
    nick = Column(String(), nullable=False, default='')

    entry_date = Column(Date())
    exit_date = Column(Date())
    email = Column(String())
    last_fee = Column(Numeric())

    fee = Column(Numeric())
    pay_interval = Column(Enum(PayInterval), nullable=False, default=PayInterval.MONTHLY)

    @hybrid_property
    def name(self):
        return "%s %s (%s)" % (self.first_name, self.last_name, self.nick)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Member({name})".format(name=self.name)
