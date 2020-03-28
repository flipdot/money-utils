#!/bin/sh
"exec" "`dirname $0`/.env/bin/python" "$0" "$@"
# coding: utf8
import logging
import sys
import typing
from datetime import date

from dateutil.relativedelta import relativedelta

import db
import util
from schema.fee_entry import FeeEntry
from schema.member import Member

import config

logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO,
    format="%(levelname) 7s %(message)s")


def main(args):
    if '--debug' in args:
        logging.getLogger('').setLevel(logging.DEBUG)

    db.init()

    end_month = date.today()
    end_month = end_month.replace(day=1)

    start_month = end_month - relativedelta(months=12)

    with db.tx() as session:
        members = session.query(Member) \
            .order_by(Member.last_name, Member.first_name)
        members_table(session, members, start_month, end_month)



def members_table(session, members, start_month, end_month, to: typing.TextIO=sys.stdout):
    months = list(util.months(start_month, end_month))

    members = members.all()
    sys.stderr.flush()
    to.flush()

    to.write('   {name:^20} | '.format(name="Name"))
    for month, next_month in months:
        to.write(' {:2}  '.format(month.month))
    to.write('\n' + '-' * (20+3 + 5*len(months)) + '\n')

    for member in members:
        to.write('{:2} '.format(member.id))
        to.write('{:>20.20} | '.format(member.name))
        for month, next_month in months:
            fees = session.query(FeeEntry)\
                .filter(FeeEntry.member_id == member.id)\
                .filter(FeeEntry.month == month).all()
            if len(fees) == 0:
                to.write('     ')
            else:
                to.write(' {:>2.0f}{:1} '.format(
                    sum([f.fee for f in fees]),
                    '' if len(fees) == 1 else len(fees)
                ))
        to.write('\n')


if __name__ == "__main__":
    sys.exit(main(sys.argv))
