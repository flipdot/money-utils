import logging
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, scoped_session

from money_utils.utils import get_config

config = get_config()

Base = declarative_base()

table_tx = "transaction"
table_member = "member"

conn = None
session_maker: sessionmaker = None


@contextmanager
def tx() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    session = session_maker()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def init(debug=False):
    global conn, session_maker, base
    if conn:
        return conn
    conn = create_engine("sqlite:///%s" % config.data_base_location)
    session_maker = scoped_session(
        sessionmaker(autocommit=False, autoflush=True, bind=conn)
    )
    Base.query = session_maker.query_property()

    if debug:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    # we use django migrations now
    with tx() as session:
        # these need to be imported!
        # noinspection PyUnresolvedReferences
        # noinspection PyUnresolvedReferences
        pass
        # Base.metadata.create_all(conn.engine)

    return conn
