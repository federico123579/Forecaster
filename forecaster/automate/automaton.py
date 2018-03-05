#!/usr/bin/env python

"""
forecaster.automate.automaton
~~~~~~~~~~~~~~

Facade class to automate algorithms.
"""

import logging
import time
from threading import Event

from forecaster.automate.positioner import Positioner
from forecaster.automate.utils import wait, wait_precisely, LogThread
from forecaster.handler import Client
from forecaster.utils import ACTIONS, TIMEFRAME, StaterChainer, read_strategy

logger = logging.getLogger('forecaster.automate')


class Automaton(StaterChainer):
    """main automaton"""

    def __init__(self, strat, predicter, mediator, preserver, successor):
        super().__init__(successor)
        self.predicter = predicter
        self.mediator = mediator
        self.preserver = preserver
        self.strategy = read_strategy(strat)['automaton']
        time_trans = self.strategy['timeframe']
        self.timeframe = [time_trans, TIMEFRAME[time_trans]]
        self.positioner = Positioner(strat, self.strategy, predicter)
        self.LOOP = Event()
        self.set_state('READY')

    def handle_request(self, event):
        self.pass_request(event)

    def start(self):
        """start threads"""
        self.LOOP.set()
        LogThread(target=self.check_closes).start()  # check closes
        logger.debug("check_closes thread started")
        self.positioner.start()
        logger.debug("positioner started")
        self.set_state('POWERED_ON')

    def stop(self):
        """stop threads"""
        self.positioner.stop()
        self.LOOP.clear()
        self.set_state('POWERED_OFF')

    def check_closes(self):
        """loop check closes"""
        wait(self._time_left(), self.LOOP)
        while self.LOOP.is_set():
            start = time.time()
            for symbol in self.strategy['currencies']:
                tran = Transaction(symbol, self)
                tran.complete()
            wait_precisely(self.strategy['sleep_transactions'], start, self.LOOP)

    def _time_left(self):
        """get time left to update of hist data"""
        # check EURUSD for convention
        hist = Client().api.get_historical_data('EURUSD', 1, self.timeframe[0])
        last_time = int(hist[0]['timestamp']) / 1000  # remove post comma milliseconds
        time_left = self.timeframe[1] - (time.time() - last_time)
        logger.debug("time left (in minutes): %f" % (time_left / 60))
        return time_left


class Transaction(object):
    def __init__(self, symbol, automaton):
        self.auto = automaton
        self.symbol = symbol
        self.mode = self._get_mode()
        self.quantity = automaton.strategy['fixed_quantity']
        self.fix = automaton.strategy['fix_trend']

    def complete(self):
        Client().refresh()
        poss = [pos for pos in Client().api.positions if pos.instrument == self.symbol]
        if self.mode == ACTIONS.BUY:
            if self.fix:  # if requested to fix
                self._fix_trend(poss, 'sell')
            self.open()
        elif self.mode == ACTIONS.SELL:
            if self.fix:  # if requested to fix
                self._fix_trend(poss, 'buy')
            self.open()
        logger.debug("transaction completed")

    def open(self):
        if not self.auto.preserver.check_margin(self.symbol, self.quantity):
            logger.warning("Transaction can't be executed due to missing funds")
        if self.mode == ACTIONS.BUY:
            Client().open_pos(self.symbol, 'buy', self.quantity)
        if self.mode == ACTIONS.SELL:
            Client().open_pos(self.symbol, 'sell', self.quantity)

    def _get_mode(self):
        return self.auto.predicter.predict(
            self.symbol, self.auto.strategy['count'], self.auto.strategy['timeframe'])

    def _fix_trend(self, poss, mode):
        pos_left = [x for x in poss if x.mode == mode]  # get position of mode
        if pos_left:  # if existent
            for pos in pos_left:  # iterate over
                Client().close_pos(pos)
