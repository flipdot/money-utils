import logging

import zmq as zmq
from django_cron import CronJobBase, Schedule

import db
import load_transactions
import members


class LoadTXsJob(CronJobBase):
    schedule = Schedule(run_every_mins=10)
    code = 'bank.load_txs_job'

    def __init__(self):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)

    def do(self):
        db.init(False)
        try:
            self.socket.bind('tcp://127.0.0.1:5555')
            load_transactions.get_transactions(False, self.tan_callback)

            members.main([])
        finally:
            self.socket.close()

    def tan_callback(self, res):
        #if self.socket.poll(5 * 60 * 1000) <= 0:
        #    logging.error("No connection got")
        #    return None

        msg = {'type': 'tan_request', 'challenge': res.challenge}
        self.socket.send_json(msg)

        if self.socket.poll(5 * 60 * 1000) <= 0:
            logging.error("No answer got")
            return None

        resp = self.socket.recv_json()
        if resp['type'] != 'tan_response':
            logging.error("Invalid response: %s", resp)
            return None
        return resp['tan']

if __name__ == "__main__":
    job = LoadTXsJob()
    job.do()
