#!/usr/bin/env python3

import logging
import sys

import db as database
import cache
from transaction import Transaction

logging.basicConfig(level=logging.INFO)

def main(args):
    db = database.get()
    cached = cache.load_cache()
    txs_cache = cached['txs']
    txs_db = database.table(database.table_tx)

    logging.info("loaded %d tx from cache, %d in db",
        len(txs_cache), txs_db.count())

    count = 0
    with db as db_tx:
        for sha, cached_tx in txs_cache.items():
            if not txs_db.find_one(_tx_id=sha):
                count += 1
                tx = Transaction(cached_tx)
                txs_db.insert(tx)
    logging.info("migrated %d tx", count)

if __name__ == "__main__":
    sys.exit(main(sys.argv))