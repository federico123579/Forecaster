#!/usr/bin/env python

"""
forecaster.mediate.mediator
~~~~~~~~~~~~~~

Facade class to mediate between client and server.
"""

import logging

from forecaster.mediate.telegram import TelegramMediator
from forecaster.utils import STATES, StaterChainer, read_strategy

logger = logging.getLogger('forecaster.mediate')


class Mediator(StaterChainer):
    """main mediator"""

    def __init__(self, strat, successor):
        super().__init__(successor)
        self.strategy = read_strategy(strat)['mediator']
        self.security = read_strategy('security')
        self.Telegram = TelegramMediator(self.security['telegram-token'], successor)
        self.set_state('READY')

    def handle_request(self, event):
        self.pass_request(event)

    def start(self):
        self.Telegram.activate()
        self.set_state('POWERED_ON')

    def stop(self):
        self.Telegram.deactivate()
        self.set_state('POWERED_OFF')

    def need_conf(self):
        self.Telegram.config_needed()
