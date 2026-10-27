"""Tests for the TAN request lifecycle and the cron job that loads transactions.

The TAN flow gates all bank access: while a TAN is pending the cron job must
not start another run, and old requests must expire so a forgotten TAN does
not block imports forever.
"""
import datetime
from unittest import mock

from django.test import TestCase

from bank.load_txs import LoadTXsJob
from bank.models import TanRequest


def make_request(when, challenge='123456', answer=None, expired=False):
    req = TanRequest.objects.create(challenge=challenge, answer=answer,
                                    expired=expired)
    # auto_now_add makes the date primary key nondeterministic; pin it
    TanRequest.objects.filter(pk=req.date).update(date=when)
    return TanRequest.objects.get(date=when)


def now():
    return datetime.datetime.now(datetime.timezone.utc)


class TanRequestTest(TestCase):
    def test_active_requests_excludes_answered_and_expired(self):
        active = make_request(now() - datetime.timedelta(hours=1))
        make_request(now() - datetime.timedelta(hours=2), answer='123456')
        make_request(now() - datetime.timedelta(hours=3), expired=True)
        self.assertEqual(list(TanRequest.active_requests()), [active])

    def test_active_requests_are_ordered_newest_first(self):
        older = make_request(now() - datetime.timedelta(hours=2))
        newer = make_request(now() - datetime.timedelta(hours=1))
        self.assertEqual(list(TanRequest.active_requests()), [newer, older])
        self.assertEqual(TanRequest.active_request(), newer)

    def test_active_request_is_none_when_all_settled(self):
        make_request(now(), answer='123456')
        self.assertIsNone(TanRequest.active_request())


class CleanOldRequestsTest(TestCase):
    def test_active_request_times_out_after_15_minutes(self):
        old = make_request(now() - datetime.timedelta(minutes=20))
        fresh = make_request(now() - datetime.timedelta(minutes=5))
        LoadTXsJob().clean_old_requests()
        old.refresh_from_db()
        fresh.refresh_from_db()
        self.assertTrue(old.expired)
        self.assertFalse(fresh.expired)

    def test_expired_requests_are_deleted_after_91_days(self):
        stale = make_request(now() - datetime.timedelta(days=100), expired=True)
        recent = make_request(now() - datetime.timedelta(days=10), expired=True)
        LoadTXsJob().clean_old_requests()
        self.assertFalse(TanRequest.objects.filter(pk=stale.date).exists())
        self.assertTrue(TanRequest.objects.filter(pk=recent.date).exists())


class LoadTXsJobDoTest(TestCase):
    def test_do_skips_while_a_tan_request_is_active(self):
        make_request(now() - datetime.timedelta(minutes=1))
        job = LoadTXsJob()
        with mock.patch('bank.load_txs.db.init') as init, \
             mock.patch('bank.load_txs.load_transactions') as load, \
             mock.patch('bank.load_txs.members') as members:
            with self.assertRaises(Exception) as ctx:
                job.do()
        self.assertIn('Skipping', str(ctx.exception))
        init.assert_not_called()
        load.assert_not_called()
        members.main.assert_not_called()

    def test_do_loads_transactions_and_analyzes_members(self):
        job = LoadTXsJob()
        with mock.patch('bank.load_txs.db.init') as init, \
             mock.patch('bank.load_txs.load_transactions') as load, \
             mock.patch('bank.load_txs.members') as members:
            job.do()
        init.assert_called_once_with(False)
        load.get_transactions.assert_called_once()
        args, _ = load.get_transactions.call_args
        self.assertIs(args[0], False)
        self.assertEqual(args[1], job.tan_callback)
        members.main.assert_called_once_with([])
