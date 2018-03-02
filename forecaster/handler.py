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
from trading212api.exceptions import *

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
        self._login()
        logger.debug("handler started")

    def _login(self):
        try:
            self.api.login(self.data['username'], self.data['password'])
        except InvalidCredentials as e:
            logger.error("Invalid credentials with %s" % e.username)
            self.set_state('MISSING_DATA')
            self.handle_request(EVENTS.MISSING_DATA)
        logger.debug("logged in")

    def open_pos(self, symbol, mode, quantity):
        """open position and handle exceptions"""
        self.refresh()  # renovate sessions
        STATE = False
        while STATE is not True:
            try:
                self.api.open_position(mode, symbol, quantity)
                STATE = True
            except PriceChangedException as e:
                continue
            except MaxQuantityExceeded as e:
                logger.warning("Maximum quantity exceeded")
                break
            except ProductNotAvaible as e:
                logger.warning("Product not avaible")
                break

    def close_pos(self, pos):
        """close position and update results"""
        self.refresh()  # renovate sessions
        STATE = False
        while STATE is not True:
            try:
                self.api.close_position(pos.id)  # close
                STATE = True
            except NoPriceException as e:
                logger.warning("NoPriceException caught")
            except ValueError as e:
                logger.warning("Position not found")
                break
        self.RESULTS += pos.result  # update returns
        self.handle_request(EVENTS.CLOSED_POS, data={'pos': pos})

    def get_last_candles(self, symbol, num, timeframe):
        candles = self.api.get_historical_data(symbol, num, timeframe)
        prices = [candle['bid'] for candle in candles]
        return prices

    def refresh(self):
        try:
            self.api.refresh()
        except RequestError as e:
            logger.warning("API unavaible")
            self._login()
            self.api.refresh()

    def set_state(self, state):
        """pattern function"""
        self.state = STATES[state]
        logger.debug("%s state: %s" % (self.__class__.__name__, STATES[state].name))

    def pass_request(self, request, **kw):
        """pattern function"""
        logger.debug("caught request: %s" % request)
        if self._successor is not None:
            self._successor.handle_request(request, **kw)
