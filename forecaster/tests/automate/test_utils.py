import logging
import threading

from forecaster.automate.utils import LogThread, ThreadHandler
from forecaster.handler import SentryClient


class TestThreading(object):
    """namespace for testing threads"""

    def test_LogThread(self, caplog):
        caplog.set_level(logging.DEBUG, logger="forecaster")
        t1 = LogThread(target=self.func_no_exc)
        t1.start()
        t1.join()
        assert "joined" in caplog.records[0].message
        # substituing captureException
        SentryClient().captureException = lambda: None
        caplog.clear()
        t2 = LogThread(target=self.func_exc)
        t2.start()
        t2.join()
        assert "assert" in [rec.message for rec in caplog.records][0]

    def test_add_thread(self, caplog):
        caplog.set_level(logging.DEBUG, logger="forecaster")
        t1 = LogThread(target=self.func_no_exc)
        ThreadHandler().add_thread(t1)
        t1.start()
        assert "appended" in caplog.records[-1].message

    def test_add_event(self, caplog):
        caplog.set_level(logging.DEBUG, logger="forecaster")
        ev = threading.Event()
        ThreadHandler().add_event(ev)
        ev.set()
        assert "appended" in caplog.records[-1].message

    def test_stop_all(self):
        ThreadHandler().stop_all()

    def func_no_exc(self):
        assert 1 / 1 == 1

    def func_exc(self):
        assert 1 / 1 == 0
