#!/usr/bin/env python

"""
forecaster.automate.automaton
~~~~~~~~~~~~~~

Facade class to automate algorithms.
"""

import logging
import time
from threading import Event, Thread

from forecaster.handler import Client
from forecaster.utils import ACTIONS, StaterChainer, read_strategy

logger = logging.getLogger('forecaster.automate.automaton')


class Automaton(StaterChainer):
    """main automaton"""

    def __init__(self, strat, predicter, mediator, successor):
        super().__init__(successor)
        self.predicter = predicter
        self.mediator = mediator
        self.strategy = read_strategy(strat)['automaton']
        self.LOOP = Event()
        self.set_state('READY')

    def handle_request(self, event):
        self.pass_request(event)

    def start(self):
        """start threads"""
        self.LOOP.set()
        Thread(target=self.check_closes).start()  # check closes
        logger.debug("check_closes thread started")
        self.set_state('POWERED_ON')

    def stop(self):
        """stop threads"""
        self.LOOP.clear()
        self.set_state('POWERED_OFF')

    def check_closes(self):
        """loop check closes"""
        self._wait(self._time_left(), self.LOOP)
        while self.LOOP.is_set():
            start = time.time()
            for symbol in self.strategy['currencies']:
                prediction = self.predicter.predict(symbol)
                tran = Transaction(symbol, prediction, self.strategy['fixed-quantity'])
                self.renew_sess()  # renovate session
                tran.complete()
                logger.debug("transaction completed")
            self._wait(self.strategy['time_to_sleep'] - (time.time() - start), self.LOOP)

    def renew_sess(self):
        Client().start()  # re-login

    def _time_left(self):
        """get time left to update of hist data"""
        # check EURUSD for convention
        hist = Client().api.get_historical_data('EURUSD', 1, self.predicter.timeframe)
        last_time = int(hist[0]['timestamp']) / 1000  # remove post comma milliseconds
        time_left = self.predicter.strategy['absolute-timeframe'] - (time.time() - last_time)
        logger.debug("time left (in minutes): %f" % (time_left / 60))
        return time_left

    def _wait(self, timeout, event):
        while timeout > 0 and event.is_set():
            time.sleep(1)
            timeout -= 1


class Transaction(object):
    def __init__(self, symbol, mode, quantity):
        self.symbol = symbol
        self.mode = mode
        self.quantity = quantity

    def complete(self):
        Client().make_transaction(self.symbol, self.mode, self.quantity)
