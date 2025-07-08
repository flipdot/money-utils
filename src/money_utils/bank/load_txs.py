import logging
import time
from threading import Thread, Event

from django_cron import CronJobBase, Schedule

from money_utils import db
from money_utils import load_transactions
from money_utils.bank import members
from money_utils.bank.models import TanRequest
from money_utils.bank.utils import ask_for_tan

import datetime as datetime_buildin

from django.utils import timezone

TIMEOUT_MINS = 2




class LoadTXsJob(CronJobBase):
    schedule = Schedule(run_every_mins=20)
    ALLOW_PARALLEL_RUNS = False
    MIN_NUM_FAILURES = 3

    code = "bank.load_txs_job"

    def do(self):
        self.clean_old_requests()

        active_request = TanRequest.active_request()
        if active_request:
            ex = Exception(
                "Skipping LoadTXsJob, because a TAN query is still active: %s"
                % active_request
            )
            logging.warning(ex)
            raise ex

        db.init(False)
        # load_transactions.get_transactions(False, self.tan_callback)
        load_transactions.get_transactions(True, self.tan_callback)
        # load_transactions.get_transactions(False, self.tan_request_handler)
        # load_transactions.get_transactions(True, self.tan_request_handler)
        logging.info("Loading transactions successful. Checking memberships...")
        members.main()

    def clean_old_requests(self):
        logging.info("Checking for old requests which should have timed out")
        old_requests = TanRequest.active_requests().filter(
            date__lte=datetime_buildin.datetime.now(tz=timezone.utc)
            - datetime_buildin.timedelta(minutes=TIMEOUT_MINS)
        )
        if old_requests:
            logging.warn("Expiring these old requests: %s", old_requests)
            old_requests.update(expired=True)

        logging.info("Checking for old requests to delete")
        old_requests = (
            TanRequest.expired_requests()
            .filter(
                date__lte=datetime_buildin.datetime.now(tz=timezone.utc)
                - datetime_buildin.timedelta(days=91)
            )
            .order_by("-date")
        )
        if old_requests:
            logging.warn("Deleting these old requests: %s", old_requests)
            old_requests.delete()

    def tan_callback(self, res):
        request = TanRequest(challenge=res.challenge, answer=None)

        if getattr(res, "challenge_hhduc", None):
            request.hhduc = res.challenge_hhduc
        if getattr(res, "challenge_matrix", None):
            request.matrix = res.challenge_matrix
        request.save()
        logging.info("Saved TanRequest %s", request)

        logging.debug("Run 'uv run answer-tan-request' on the machine or take a look in the admin web interface")
        start_time = time.monotonic()
        while (request.answer is None) and (
            time.monotonic() - start_time < 60 * TIMEOUT_MINS
        ):
            request.refresh_from_db()
            if request.answer is not None:
                logging.info("Got TAN answer %s %s", request, request.answer)
                return request.answer
            logging.info("waiting for tan answer")
            time.sleep(1)
        logging.warning("TAN request timed out after %s mins.", TIMEOUT_MINS)
        request.expired = True
        request.save()
        return None

    def tan_request_handler(self, res):
        """
        Handles the TAN request process, including saving the request,
        starting a thread to fetch the TAN answer, and waiting for the answer.
        """
        try:
            # Initialize and save the TAN request
            request = TanRequest(challenge=res.challenge, answer=None)
            if hasattr(res, "challenge_hhduc"):
                request.hhduc = res.challenge_hhduc
            if hasattr(res, "challenge_matrix"):
                request.matrix = res.challenge_matrix
            request.save()
            logging.info("Saved TanRequest: %s", request)
    
            # Event to signal when the answer is ready or when we should stop waiting
            stop_event = Event()
    
            def get_tan_answer():
                """
                Fetches the TAN answer asynchronously by calling ask_tan_callback.
                """
                try:
                    answer = ask_for_tan(None, res)
                    if answer:
                        request.answer = answer
                        request.save()
                        logging.info("Updated TanRequest with answer: %s", request)
                except Exception as e:
                    logging.error("Error while getting TAN answer: %s", e)
                finally:
                    # Signal that we're done, whether successful or not
                    stop_event.set()
    
            # Start a separate thread to get the TAN answer
            tan_thread = Thread(target=get_tan_answer, daemon=True)
            tan_thread.start()
    
            # Wait for the TAN answer with a timeout
            start_time = time.monotonic()
            timeout_seconds = 60 * TIMEOUT_MINS
    
            while time.monotonic() - start_time < timeout_seconds:
                # Wait for the stop event or timeout
                if stop_event.wait(timeout=1):  # Wait for 1 second at a time
                    break
                
                request.refresh_from_db()  # Refresh from database to check for updates
                if request.answer:
                    logging.info("Received TAN answer: %s", request.answer)
                    return request.answer
                
                logging.debug("Waiting for TAN answer...")
    
            # Handle timeout or completion
            if not stop_event.is_set():
                logging.warning("TAN request timed out after %d minutes.", TIMEOUT_MINS)
                request.expired = True
                request.save()
            
            # Ensure the thread is properly joined
            tan_thread.join(timeout=1)  # Give the thread 1 second to finish
            if tan_thread.is_alive():
                logging.warning("TAN thread did not complete in time.")
    
            return request.answer if request.answer else None
    
        except Exception as e:
            logging.error("Error in tan_request_handler: %s", e)
            return None
    
