import sqlalchemy

import config
import dataset

table_tx = 'transaction'
table_member = 'member'

conn = None

def get():
    global conn
    if conn: return conn
    conn = dataset.connect('sqlite:///%s' % config.db_path)
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