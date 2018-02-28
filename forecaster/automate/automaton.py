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
from forecaster.utils import ACTIONS, TIMEFRAME, StaterChainer, read_strategy

logger = logging.getLogger('forecaster.automate')


class Automaton(StaterChainer):
    """main automaton"""

    def __init__(self, strat, predicter, mediator, successor):
        super().__init__(successor)
        self.predicter = predicter
        self.mediator = mediator
        self.strategy = read_strategy(strat)['automaton']
        self.timeframe = self.strategy['position_timeframe']
        self.timeframe_converted_trans = TIMEFRAME[self.predicter.timeframe]
        self.timeframe_converted_pos = TIMEFRAME[self.timeframe]
        self.LOOP = Event()
        self.set_state('READY')

    def handle_request(self, event):
        self.pass_request(event)

    def start(self):
        """start threads"""
        self.LOOP.set()
        Thread(target=self.check_closes).start()  # check closes
        logger.debug("check_closes thread started")
        Thread(target=self.check_positions).start()  # check positions
        logger.debug("check_positions thread started")
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
                tran = Transaction(symbol, prediction, self.strategy['fixed_quantity'])
                tran.complete()
                logger.debug("transaction completed")
            self._wait_precisely(self.strategy['sleep_transactions'], start, self.LOOP)

    def check_positions(self):
        """check positions if cross bolliger band"""
        # get count of candles
        count = int(self.timeframe_converted_trans / self.timeframe_converted_pos) * \
            sefl.predicter.strategy['count']
        while self.LOOP.is_set() and self.strategy['check_positions']:
            start = time.time()
            Client().refresh()
            for pos in Client().api.account.positions:
                # predict bolliger band more accurate
                candles = Client().get_last_candles(pos.instrument, count, self.timeframe)
                band = self.predicter.MeanReversion.get_band(candles)
                if pos.mode == 'buy':
                    if pos.current_price >= band:
                        Client().close_pos(pos)
                elif pos.mode == 'sell':
                    if pos.current_price <= band:
                        Client().close_pos(pos)
            logger.debug("checked positions")
            self._wait_precisely(self.strategy['sleep_positions'], start, self.LOOP)

    def _time_left(self):
        """get time left to update of hist data"""
        # check EURUSD for convention
        hist = Client().api.get_historical_data('EURUSD', 1, self.predicter.timeframe)
        last_time = int(hist[0]['timestamp']) / 1000  # remove post comma milliseconds
        time_left = self.timeframe_converted - (time.time() - last_time)
        logger.debug("time left (in minutes): %f" % (time_left / 60))
        return time_left

    def _wait_precisely(self, timeout, start_time, event):
        """wait precisely timeout in relation of start time"""
        self._wait(timeout - (time.time() - start_time), event)

    def _wait(self, timeout, event):
        """wait until loop or timeout clears"""
        logger.debug("sleeping for %d seconds" % int(timeout))
        start = time.time()
        while time.time() - start <= timeout and event.is_set():
            time.sleep(0.1)


class Transaction(object):
    def __init__(self, symbol, mode, quantity):
        self.symbol = symbol
        self.mode = mode
        self.quantity = quantity

    def complete(self):
        Client().make_transaction(self.symbol, self.mode, self.quantity)
