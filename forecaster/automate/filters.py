#!/usr/bin/env python

"""
forecaster.automate.filters
~~~~~~~~~~~~~~

Contains all position filters.
"""
import logging
import time

from forecaster.automate.utils import ACTIONS
from forecaster.handler import Client
from forecaster.patterns import Chainer

logger = logging.getLogger('forecaster.automate.filter')


class FilterWrapper(Chainer):
    """wrapper for filters"""

    def __init__(self, strat, positioner):
        super().__init__(positioner)
        self.strat = strat
        self.damper = Damper(strat['damper']['max'], strat['damper']['timeout'])
        logger.debug("FilterWrapper initied")

    def handle_request(self, event, **kw):
        if event == ACTIONS.CLOSE:
            Client().close_pos(kw['pos'])
        elif event == ACTIONS.KEEP:
            logger.debug("keeping position %s" % kw['pos'].id)
        else:
            self.pass_request(event, **kw)

    def check(self, pos):
        if self.strat['damper']['activate']:
            self.handle_request(self.damper.check(pos), pos=pos)
        else:
            self.handle_request(ACTIONS.CLOSE, pos=pos)


# +----------------------------------------------------------------------+
# | complexity_level: 1                                                  |
# | Attend various attemp and amortize                                   |
# +----------------------------------------------------------------------+
class Damper(object):
    """damper filter"""

    def __init__(self, mx, timeout):
        self.max = mx  # max tries
        self.timeout = timeout
        self.positions = {}
        self.times = {}
        logger.debug("Damper filter initied")

    def check(self, pos):
        self._add(pos)  # check position
        if self.positions[pos.id] > 0 and pos.result <= 0:  # if negative and other tries
            time_elaps = time.time() - self.times[pos.id]
            if time_elaps < self.timeout:  # if short time
                logger.debug("time left: %d seconds" % (self.timeout - time_elaps))
                return ACTIONS.KEEP
            self.positions[pos.id] -= 1  # countdown
            self.times[pos.id] = time.time()  # set timeout time
            logger.debug("keep left for %s: %d" % (pos.instrument, self.positions[pos.id]))
            return ACTIONS.KEEP
        else:
            del self.positions[pos.id]
            return ACTIONS.CLOSE

    def _add(self, pos):
        if pos.id not in self.positions:
            self.positions[pos.id] = self.max
        if pos.id not in self.times:
            self.times[pos.id] = 0
