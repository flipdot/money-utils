#!/usr/bin/env python3

import logging
import sys

import db as database
import cache
from schema.transaction import Transaction

logging.basicConfig(level=logging.INFO)

def main(args):
    db = database.init()
    cached = cache.load_cache()
    txs_cache = cached['txs']

    count = 0
    with database.tx() as session:
        logging.info("loaded %d tx from cache, %d in db",
            len(txs_cache), session.query(Transaction).count())

        for sha, cached_tx in txs_cache.items():
            if not session.query(Transaction).filter_by(_tx_id=sha).first():
                count += 1
                tx = Transaction(cached_tx)
                session.add(tx)
    logging.info("migrated %d tx", count)

if __name__ == "__main__":
    sys.exit(main(sys.argv))