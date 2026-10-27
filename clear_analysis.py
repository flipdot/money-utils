import logging
import sys

from sqlalchemy import update

import db
from schema.transaction import Transaction
import config

logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO,
    format="%(levelname) 7s %(message)s")


def main(args):
    if '--debug' in args:
        logging.getLogger('').setLevel(logging.DEBUG)

    db.init()

    with db.tx() as session:
        session.execute(update(Transaction).values(
            member_id=None, type=None))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
