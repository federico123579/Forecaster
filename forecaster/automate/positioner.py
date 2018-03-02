#!/usr/bin/env python

"""
forecaster.automate.positioner
~~~~~~~~~~~~~~

Class to handle positions.
"""
import logging
import time
from threading import Event, Thread

from forecaster.automate.utils import wait_precisely
from forecaster.handler import Client
from forecaster.utils import TIMEFRAME, read_strategy

logger = logging.getLogger('forecaster.automate.positioner')


class Positioner(object):
    """handle all positions"""

    def __init__(self, strat, auto_strat, preserver):
        self.preserver = preserver
        self.strategy = read_strategy(strat)['positioner']
        self.auto_strat = auto_strat
        # make a check table
        self.pos_checks = {x[0]: x[1]['activate'] for x in self.strategy.items()}
        self.CHECKS = {'REV': Event(), 'SECURITY': Event()}
        logger.debug("Positioner initied")

    def start(self):
        # MEAN REVERSION CHECK POSITIONS
        if self.pos_checks['reversion']:
            self.CHECKS['REV'].set()  # activate
            Thread(target=self.reversion_check).start()
            logger.debug("reversion position handler launched")
        # SECURITY CHECK POSITIONS
        if self.pos_checks['security-relative']:
            self.CHECKS['SECURITY'].set()  # activate
            Thread(target=self.security_relative_check).start()
            logger.debug("security-relative position handler launched")
        if self.pos_checks['security-fixed']:
            self.CHECKS['SECURITY'].set()  # activate
            Thread(target=self.security_fixed_check).start()
            logger.debug("security-fixed position handler launched")

    def stop(self):
        # clear all events
        for ev in self.CHECKS.values():
            ev.clear()

    def reversion_check(self):
        """check loop for reversion"""
        _strat = self.strategy['reversion']
        self._make_check_loop(self._rev_check, self.CHECKS['REV'], _strat['sleep'])

    def _rev_check(self, pos):
        _strat = self.strategy['reversion']
        # get number of candles
        count = int(TIMEFRAME[self.auto_strat['timeframe']] /
                    TIMEFRAME[_strat['timeframe']]) * self.auto_strategy['count']
        candles = Client().get_last_candles(  # get candles
            pos.instrument, count, _strat['timeframe'])
        self.predicter.check_position(pos, candles)  # check position

    def security_relative_check(self):
        """check loop for stop limits relative"""
        _strat = self.strategy['security-relative']
        self._make_check_loop(self.preserver.check_position_relative,
                              self.CHECKS['SECURITY'], _strat['sleep'])

    def security_fixed_check(self):
        """check loop for stop limits fixed"""
        _strat = self.strategy['security-fixed']
        self._make_check_loop(self.preserver.check_position_fixed,
                              self.CHECKS['SECURITY'], _strat['sleep'])

    def _make_check_loop(self, func, event, sleep):
        """checkp positions loop"""
        while event.is_set():
            start = time.time()  # record timing
            for pos in Client().api.account.positions:
                Client().refresh()  # refresh and update
                func(pos)
            wait_precisely(sleep, start, event)  # wait and repeat
