#!/usr/bin/env python

"""
forecaster.automate.automaton
~~~~~~~~~~~~~~

Facade class to automate algorithms.
"""

import logging
import time
from threading import Event, Thread

from forecaster.automate.positioner import Positioner
from forecaster.automate.utils import wait, wait_precisely
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
        self.positioner = Positioner(strat, self.strategy, preserver)
        self.LOOP = Event()
        self.set_state('READY')

    def handle_request(self, event):
        self.pass_request(event)

    def start(self):
        """start threads"""
        self.LOOP.set()
        Thread(target=self.check_closes).start()  # check closes
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
                prediction = self.predicter.predict(
                    symbol, self.strategy['count'], self.strategy['timeframe'])
                tran = Transaction(symbol, prediction, self.strategy['fixed_quantity'])
                tran.complete(self.strategy['fix_trend'])
                logger.debug("transaction completed")
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
    def __init__(self, symbol, mode, quantity):
        self.symbol = symbol
        self.mode = mode
        self.quantity = quantity

    def complete(self, fix=False):
        Client().refresh()
        poss = [pos for pos in Client().api.positions if pos.instrument == self.symbol]
        if self.mode == ACTIONS.BUY:
            if fix:  # if requested to fix
                self._fix_trend(poss, 'sell')
            Client().open_pos(self.symbol, 'buy', self.quantity)
        elif self.mode == ACTIONS.SELL:
            if fix:  # if requested to fix
                self._fix_trend(poss, 'buy')
            Client().open_pos(self.symbol, 'sell', self.quantity)

    def _fix_trend(self, poss, mode):
        pos_left = [x for x in poss if x.mode == mode]  # get position of mode
        if pos_left:  # if existent
            for pos in pos_left:  # iterate over
                self.close_pos(pos)
