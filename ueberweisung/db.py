from contextlib import contextmanager

import dataset
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, scoped_session

import config

Base = declarative_base()

table_tx = 'transaction'
table_member = 'member'

conn = None
session_maker: sessionmaker = None


@contextmanager
def tx() -> Session:
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

def get():
    global conn, session_maker, base
    if conn: return conn
    conn = dataset.connect('sqlite:///%s' % config.db_path)
    session_maker = scoped_session(sessionmaker(autocommit=False,
            autoflush=False,
            bind=conn.engine))
    Base.query = session_maker.query_property()

    with tx() as session:
        import schema
        Base.metadata.create_all(conn.engine)

    return conn

def table(which: str) -> dataset.Table:
    db = get()
    pkey = None, None
    if which == table_tx:
        pkey = "_tx_id", db.types.string
    table = db.create_table(which, primary_id=pkey[0], primary_type=pkey[1])

    if which == table_tx:
        table.create_column('amount', sqlalchemy.Numeric)

    return table
