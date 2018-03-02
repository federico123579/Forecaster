#!/usr/bin/env python

"""
forecaster.automate.utils
~~~~~~~~~~~~~~

Locals utils in automate model.
"""

import logging
import time

logger = logging.getLogger('forecaster.automate.utils')


def wait_precisely(timeout, start_time, event):
    """wait precisely timeout in relation of start time"""
    wait(timeout - (time.time() - start_time), event)


def wait(timeout, event):
    """wait until loop or timeout clears"""
    logger.debug("sleeping for %d seconds" % int(timeout))
    start = time.time()
    while time.time() - start <= timeout and event.is_set():
        time.sleep(0.1)
