import re
from typing import Iterable
from hashlib import sha1
from .models import Transaction

drinks_regex = r"^drinks?\s+(?P<uid>\d+)(\s+(?P<info>.*))?$"
drinks_pattern = re.compile(drinks_regex, re.I)


def get_recharges():
    txs: Iterable[Transaction] = Transaction.objects.filter(
        purpose__iregex=drinks_regex
    )
    recharges_by_uid = {}
    for tx in txs:
        match = drinks_pattern.match(tx.purpose)
        uid = match.group("uid")
        amount = str(tx.amount)
        tx_date = str(tx.date)
        if uid not in recharges_by_uid:
            recharges_by_uid[uid] = []
        info = sha1(tx.purpose.encode("utf8")).hexdigest()
        r = {"uid": uid, "info": info, "amount": amount, "date": tx_date}
        recharges_by_uid[uid].append(r)
    # sort all
    for uid in recharges_by_uid:
        recharges_by_uid[uid] = sorted(recharges_by_uid[uid], key=lambda r: r["date"])
    return recharges_by_uid
