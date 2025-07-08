from sqlalchemy import Column, String, DateTime

from money_utils.db import Base

LAST_LOAD = "last_load"


class Status(Base):
    __tablename__ = "status"
    key = Column(String(), primary_key=True)

    value_str = Column(String())
    value_dt = Column(DateTime())
