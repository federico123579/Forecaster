#!/usr/bin/env python

"""
forecaster.automate.utils
~~~~~~~~~~~~~~

Locals utils in automate model.
"""
import logging
import time
from enum import Enum, auto
from threading import Thread

logger = logging.getLogger('forecaster.automate.utils')


class ACTIONS(Enum):
    CLOSE = auto()
    KEEP = auto()


def wait_precisely(timeout, start_time, event):
    """wait precisely timeout in relation of start time"""
    wait(timeout - (time.time() - start_time), event)


def wait(timeout, event):
    """wait until loop or timeout clears"""
    logger.debug("sleeping for %d seconds" % int(timeout))
    start = time.time()
    while time.time() - start <= timeout and event.is_set():
        time.sleep(0.1)


class LogThread(Thread):
    """Thread class to handle errors"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._real_run = self.run
        self.run = self._wrap_run

    def _wrap_run(self):
        try:
            self._real_run()
        except Exception as e:
            logging.exception("Exception in thread: %s" % e)
