import logging
import time

from django_cron import CronJobBase, Schedule

import db
import load_transactions
import members
from bank.models import TanRequest

from datetime import timedelta
from django.utils.datetime_safe import datetime

TIMEOUT_MINS = 15


class LoadTXsJob(CronJobBase):
    schedule = Schedule(run_every_mins=20)
    ALLOW_PARALLEL_RUNS = False
    MIN_NUM_FAILURES = 3

    code = 'bank.load_txs_job'

    def do(self):
        self.clean_old_requests()

        active_request = TanRequest.active_request()
        if active_request:
            ex = Exception(
                "Skipping LoadTXsJob, because a TAN query is still active: %s" % active_request)
            logging.warning(ex)
            raise ex

        db.init(False)
        load_transactions.get_transactions(False, self.tan_callback)
        logging.info(
            "Loading transactions successful. Checking memberships...")
        members.main([])

    def clean_old_requests(self):
        logging.info("Checking for old requests which should have timed out")
        old_requests = TanRequest.active_requests()\
            .filter(date__lte=datetime.utcnow() - timedelta(minutes=TIMEOUT_MINS))
        if old_requests:
            logging.warn("Expiring these old requests: %s", old_requests)
            old_requests.update(expired=True)

        logging.info("Checking for old requests to delete")
        old_requests = TanRequest.expired_requests()\
            .filter(date__lte=datetime.utcnow() - timedelta(days=91))\
            .order_by('-date')
        if old_requests:
            logging.warn("Deleting these old requests: %s", old_requests)
            old_requests.delete()

    def tan_callback(self, res):
        request = TanRequest(challenge=res.challenge, answer=None)

        if getattr(res, 'challenge_hhduc', None):
            request.hhduc = res.challenge_hhduc
        request.save()
        logging.info("Saved TanRequest %s", request)

        start_time = time.monotonic()
        while (not request.answer) and (time.monotonic() - start_time < 60 * TIMEOUT_MINS):
            request.refresh_from_db()
            if request.answer:
                logging.info("Got TAN answer %s %s", request, request.answer)
                return request.answer
            time.sleep(1)
        logging.warning("TAN request timed out after %s mins.", TIMEOUT_MINS)
        request.expired = True
        request.save()
        return None
