"""
forecaster.automate.utils
~~~~~~~~~~~~~~

Locals utils in automate model.
"""

import logging
import time
from enum import Enum, auto
from threading import Thread, Event

from forecaster.handler import SentryClient
from forecaster.patterns import Singleton

LOGGER = logging.getLogger('forecaster.automate.utils')


class ACTIONS(Enum):
    CLOSE = auto()
    KEEP = auto()


def wait_precisely(timeout, start_time, event):
    """wait precisely timeout in relation of start time"""
    wait(timeout - (time.time() - start_time), event)


def wait(timeout, event):
    """wait until loop or timeout clears"""
    LOGGER.debug("sleeping for {} seconds".format(int(timeout)))
    start = time.time()
    while time.time() - start <= timeout and event.is_set():
        time.sleep(0.1)


class LogThread(Thread):
    """Thread class to handle errors"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._real_run = self.run
        self.run = self._wrap_run
        self._real_join = self.join
        self.join = self._wrap_join

    def _wrap_run(self):
        try:
            self._real_run()
        except Exception as e:
            LOGGER.exception("Exception in thread: {}".format(e))
            SentryClient().captureException()

    def _wrap_join(self, *args, **kwargs):
        self._real_join(*args, **kwargs)
        LOGGER.debug("thread: {!s} - joined".format(self))


class ThreadHandler(metaclass=Singleton):
    def __init__(self):
        self.handlers = []
        self.events = []
        LOGGER.debug("ThreadHandler initied")

    def add_thread(self, thr):
        """add thread"""
        if thr in self.handlers:
            LOGGER.debug("thread: {!s} - already added".format(thr))
            return
        if isinstance(thr, Thread):
            self.handlers.append(thr)
            LOGGER.debug("thread: {!s} - appended".format(thr))
        else:
            raise ValueError("{} is not a thread".format(thr))

    def add_event(self, event):
        """add event"""
        if event in self.events:
            LOGGER.debug("event: {!s} - already added".format(event))
            return
        if isinstance(event, Event):
            self.events.append(event)
            LOGGER.debug("event: {!s} - appended".format(event))
        else:
            raise ValueError("{} is not an event".format(event))

    def stop_all(self, timeout=None):
        """stop all events"""
        for ev in self.events:
            ev.clear()
            LOGGER.debug("event: {!s} - cleared".format(ev))
        for thr in self.handlers:
            thr.join(timeout)
            if not isinstance(thr, LogThread):
                LOGGER.debug("thread: {!s} - joined".format(thr))
