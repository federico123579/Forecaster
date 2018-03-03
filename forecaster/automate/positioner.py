#!/usr/bin/env python

"""
forecaster.automate.positioner
~~~~~~~~~~~~~~

Class to handle positions.
"""
import logging
import time
from enum import Enum, auto
from threading import Event, Thread

from forecaster.automate.utils import wait_precisely
from forecaster.handler import Client
from forecaster.utils import TIMEFRAME, Chainer, read_strategy

logger = logging.getLogger('forecaster.automate.positioner')


class ACTION(Enum):
    CLOSE = auto()
    KEEP = auto()


class Positioner(Chainer):
    """handle all positions"""

    def __init__(self, strat, auto_strat, preserver):
        self.preserver = preserver
        strat = read_strategy(strat)
        self.strategy = strat['positioner']
        self.auto_strategy = auto_strat
        self.Filter = FilterWrapper(strat['filter'])
        # make a check table
        self.pos_checks = {x[0]: x[1]['activate'] for x in self.strategy.items()}
        self.CHECKS = {'REV': Event(), 'SECURITY': Event()}
        logger.debug("Positioner initied")

    def handle_request(self, event, **kw):
        if event == ACTION.CLOSE:
            self.Filter.check(kw['pos'])  # pass to filters

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

    # --[ POSITION LOOP CHECKS ]--
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
        return self.predicter.check_position(pos, candles)  # check position

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
        """check positions loop"""
        while event.is_set():
            start = time.time()  # record timing
            for pos in Client().api.account.positions:
                Client().refresh()  # refresh and update
                action = func(pos)
                self.handle_request(action, pos=pos)
            wait_precisely(sleep, start, event)  # wait and repeat


class FilterWrapper(Chainer):
    """wrapper for filters"""

    def __init__(self, strat):
        self.strat = strat
        self.damper = Damper(strat['damper']['max'], strat['damper']['timeout'])
        logger.debug("FilterWrapper initied")

    def handle_request(self, event, **kw):
        if event == ACTION.CLOSE:
            Client().close_pos(kw['pos'])
        elif event == ACTION.KEEP:
            logger.debug("keeping position %s" % kw['pos'].id)
            pass

    def check(self, pos):
        if self.strat['damper']['activate']:
            self.handle_request(self.damper.check(pos), pos=pos)
        else:
            self.handle_request(ACTION.CLOSE, pos=pos)


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
        if self.positions[pos.id] >= 0 and pos.result <= 0:  # if negative and other tries
            if time.time() - self.times[pos.id] < self.timeout:  # if short time
                return ACTION.KEEP
            self.positions[pos.id] -= 1  # countdown
            self.times[pos.id] = time.time()  # set timeout time
            logger.debug("keep left for %s: %d" % (pos.instrument, self.positions[pos]))
            return ACTION.KEEP
        else:
            return ACTION.CLOSE

    def _add(self, pos):
        if pos not in self.positions:
            self.positions[pos.id] = 0
        if pos not in self.times:
            self.times[pos.id] = 0
