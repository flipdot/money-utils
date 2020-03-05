import logging
import time

from django_cron import CronJobBase, Schedule

import db
import load_transactions
import members
from bank.models import TanRequest


class LoadTXsJob(CronJobBase):
    schedule = Schedule(run_every_mins=20)
    code = 'bank.load_txs_job'

    def do(self):
        db.init(False)
        load_transactions.get_transactions(False, self.tan_callback)

        members.main([])

    def tan_callback(self, res):

        request = TanRequest()
        request.challenge = res.challenge
        if getattr(res, 'challenge_hhduc', None):
            request.hhduc = res.challenge_hhduc
        request.save()

        start_time = time.monotonic()
        while (not request.answer) and (time.monotonic() - start_time < 60 * 5):
            request.refresh_from_db()
            if request.answer:
                logging.info("Got TAN answer %s %s", request, request.answer)
                return request.answer
            time.sleep(1)
        logging.warning("TAN request timed out after 5 mins.")
        request.expired = True
        request.save()
        return None
