#!/usr/bin/env python

"""
forecaster.handler
~~~~~~~~~~~~~~

Handle requests and responses from API
"""
import logging

import trading212api
from forecaster.exceptions import MissingData
from forecaster.utils import ACTIONS, EVENTS, STATES, Singleton, read_strategy

logger = logging.getLogger('forecaster.handler')


class Client(metaclass=Singleton):
    """UI with APIs"""

    def __init__(self, strat, successor=None):
        self._successor = successor
        self.state = STATES.POWERED_OFF
        self.RESULTS = 0.0  # results
        self.strategy = read_strategy(strat)['handler']
        self.api = trading212api.Client(self.strategy['mode'])
        self.set_state('READY')
        logger.debug("handler initied")

    def handle_request(self, event, **kw):
        """pattern function"""
        self.pass_request(event, **kw)

    def start(self):
        try:
            self.data = read_strategy('data')
        except FileNotFoundError:
            raise MissingData()
        try:
            self.api.login(self.data['username'], self.data['password'])
        except trading212api.exceptions.InvalidCredentials as e:
            logger.error("Invalid credentials with %s" % e.username)
            self.set_state('MISSING_DATA')
            self.handle_request(EVENTS.MISSING_DATA)
        logger.debug("handler started")

    def make_transaction(self, symbol, mode, quantity):
        self.api.refresh()
        poss = [pos for pos in self.api.positions if pos.instrument == symbol]
        if mode == ACTIONS.BUY:
            self._fix_trend(poss, 'sell')
            self._open_pos(symbol, 'buy', quantity)
        elif mode == ACTIONS.SELL:
            self._fix_trend(poss, 'buy')
            self._open_pos(symbol, 'sell', quantity)

    def _open_pos(self, symbol, mode, quantity):
        STATE = False
        while STATE is not True:
            try:
                self.api.open_position(mode, symbol, quantity)
                STATE = True
            except trading212api.exceptions.PriceChangedException as e:
                continue
            except trading212api.exceptions.MaxQuantityExceeded as e:
                logger.warning("Maximum quantity exceeded")
                break

    def _fix_trend(self, poss, mode):
        pos_left = [x for x in poss if x.mode == mode]  # get position of mode
        if pos_left:  # if existent
            for pos in pos_left:  # iterate over
                self.api.close_position(pos.id)  # close
                self.RESULTS += pos.result  # update returns
                self.handle_request(EVENTS.CLOSED_POS, data={'pos': pos})

    def get_last_closes(self, symbol, num, timeframe):
        candles = self.api.get_historical_data(symbol, num, timeframe)
        closes = [candle['bid']['close'] for candle in candles]
        return closes

    def set_state(self, state):
        """pattern function"""
        self.state = STATES[state]
        logger.debug("%s state: %s" % (self.__class__.__name__, STATES[state].name))

    def pass_request(self, request, **kw):
        """pattern function"""
        logger.debug("caught request: %s" % request)
        if self._successor is not None:
            self._successor.handle_request(request, **kw)
