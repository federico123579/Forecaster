#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
forecaster.bot
~~~~~~~~~~~~~~

The Bot Client class.
"""

import logging
import os
import signal

from forecaster.automate import Automaton
from forecaster.automate.utils import ThreadHandler
from forecaster.enums import ACTIONS, EVENTS, STATUS
from forecaster.handler import Client, SentryClient
from forecaster.mediate import Mediator
from forecaster.patterns import Chainer
from forecaster.predict import Predicter

LOGGER = logging.getLogger('forecaster.bot')

# EVENTS COLLECTIONS
MEDIATE_EVENTS = [
    EVENTS.CLOSED_ALL_POS,
    EVENTS.CLOSED_POS,
    EVENTS.MARKET_CLOSED,
    EVENTS.PRODUCT_NOT_AVAIBLE,
    EVENTS.MISSING_DATA,
    EVENTS.OPENED_POS]


class Bot(Chainer):
    """Mediator for every component and head of chaining of resposabilities"""

    def __init__(self, strat='default'):
        super().__init__()
        # LEVEL ZERO - access to apis and track errors
        self.sentry = SentryClient()
        self.client = Client(self)
        self.mediate = Mediator(self)
        # LEVEL ONE - algorithmic core
        self.predict = Predicter(self)
        # LEVEL TWO - automation
        self.automate = Automaton(self)

    def handle_request(self, request, **kw):
        """handle requests from chainers"""
        # start the bot
        if request == ACTIONS.START_BOT:
            self.start_bot()
        # stop the bot
        elif request == ACTIONS.STOP_BOT:
            self.stop_bot()
        # shutdown the foreground
        elif request == ACTIONS.SHUTDOWN:
            self.stop()
        # get prediction
        elif request == ACTIONS.PREDICT:
            return self.predict.predict(*kw['args'])
        # get score
        elif request == ACTIONS.SCORE:
            return self.predict.get_score(*kw['args'])
        # notify handler
        elif request == ACTIONS.CHANGE_MODE:
            return self.client.change_mode(kw['mode'])
        # swap mode
        elif request == EVENTS.MODE_FAILURE:
            LOGGER.warning("Mode failed to login")
            self.client.swap()
        # assign to mediator
        elif request in MEDIATE_EVENTS:
            self.echo_request(self.mediate, request, **kw)
        # connection error
        elif request == EVENTS.CONNECTION_ERROR:
            self.mediate.log("Connection error caught")
            self.handle_request(ACTIONS.STOP_BOT)
            self.mediate.log("Bot stopped")
            raise

    def start(self):
        """start cycle"""
        # first level: interface for receiving commands
        self.mediate.start()
        self.status = STATUS.READY
        LOGGER.debug("BOT: ready")

    def stop(self):
        self.automate.stop()
        self.mediate.stop()
        ThreadHandler().stop_all()
        LOGGER.debug("BOT: shutted down")
        os.kill(os.getpid(), signal.SIGINT)

    def idle(self):
        LOGGER.debug("BOT: idling")
        self.mediate.idle()

    def start_bot(self):
        """start bot cycle"""
        if self.status == STATUS.ON:
            LOGGER.warning("BOT: already started")
            return
        self.client.start()
        self.automate.start()
        self.status = STATUS.ON
        LOGGER.debug("BOT: started")

    def stop_bot(self):
        if self.status == STATUS.OFF:
            LOGGER.warning("BOT: already stopped")
            return
        self.automate.stop()
        self.status = STATUS.OFF
        LOGGER.debug("BOT: stopped")
