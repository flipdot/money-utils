from sqlalchemy import Column, Integer, String, Numeric, Date
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

class Member(Base):
    __tablename__ = 'member'
    id = Column(Integer, primary_key=True)
    first_name = Column(String())
    last_name = Column(String())
    entry_date = Column(Date())
    exit_date = Column(Date())
    email = Column(String())
    last_fee = Column(Numeric())

    @hybrid_property
    def name(self):
        return self.first_name + " " + self.last_name