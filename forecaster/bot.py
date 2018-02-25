#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
forecaster.bot
~~~~~~~~~~~~~~

The Bot Client class.
"""
import logging

from forecaster.exceptions import *
from forecaster.handler import Client
from forecaster.mediate import Mediator
from forecaster.predict import Predicter
from forecaster.utils import EVENTS, STATES, StaterChainer, read_strategy

logger = logging.getLogger('forecaster.bot')


class Bot(StaterChainer):
    """main controller"""

    def __init__(self, strat):
        super().__init__()
        self.strategy = read_strategy(strat)
        self.handler = Client(strat, self)
        self.mediate = Mediator(strat, self)
        self.predict = Predicter(strat)

    def handle_request(self, event):
        if event == EVENTS.START_BOT:
            self.start_bot()
        elif event == EVENTS.STOP_BOT:
            self.stop_bot()
        elif event == EVENTS.MISSING_DATA:
            self.mediate.need_conf()

    def start(self):
        """start cycle"""
        # first level: interface for receiving commands
        self.mediate.start()
        self.set_state('READY')
        logger.debug("bot listening")

    def stop(self):
        self.mediate.stop()
        self.set_state('POWERED_OFF')

    def start_bot(self):
        """start bot cycle"""
        while self.state is not STATES.POWERED_ON:
            try:
                # second level: client with APIs
                self.handler.start()
                self.set_state('POWERED_ON')
            except MissingData as e:
                self.set_state('MISSING_DATA')
                self.handle_request(EVENTS.MISSING_DATA)

    def stop_bot(self):
        # TODO: AUTOMATA STOP
        self.set_state('STOPPED')
