import logging
import sys

import db
from schema.transaction import Transaction

logging.basicConfig(level=logging.INFO, format="%(levelname) 7s %(message)s")


def main(args):
    if '--debug' in args:
        logging.getLogger('').setLevel(logging.DEBUG)

    db.init()

    with db.tx() as session:
        session.query(Transaction)\
            .update({'member_id': None, 'type': None})


if __name__ == "__main__":
    sys.exit(main(sys.argv))
