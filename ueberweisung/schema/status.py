from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

from db import Base

LAST_LOAD = "last_load"

class Status(Base):
    __tablename__ = 'status'
    key = Column(String(), primary_key=True)

    value_str = Column(String())
    value_dt = Column(DateTime())
