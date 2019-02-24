from django_cron import CronJobBase, Schedule

import db
import load_transactions
import members


class LoadTXsJob(CronJobBase):
    schedule = Schedule(run_every_mins=1)
    code = 'bank.load_txs_job'

    def do(self):
        db.init(False)
        load_transactions.get_transactions(False)

        members.main([])
