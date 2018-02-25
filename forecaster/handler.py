#!/usr/bin/env python

"""
forecaster.handler
~~~~~~~~~~~~~~

Handle requests and responses from API
"""
import logging

import trading212api
from forecaster.exceptions import MissingData
from forecaster.utils import EVENTS, STATES, Singleton, read_strategy

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

    def handle_request(self, event):
        self.pass_request(event)

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
        logger.debug("hanlder started")

    def set_state(self, state):
        """log state"""
        self.state = STATES[state]
        logger.debug("%s state: %s" % (self.__class__.__name__, STATES[state].name))

    def pass_request(self, request, **kwargs):
        logger.debug("caught request: %s" % request)
        if self._successor is not None:
            self._successor.handle_request(request)
