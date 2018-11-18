from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Member(Base):
    __tablename__ = 'member'
    id = Column(Integer, primary_key=True)
    name = Column(String())
    email = Column(String())
    last_fee = Column(Numeric())

