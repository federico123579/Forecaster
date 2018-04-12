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
        self.predict = Predicter('predict', self)
        # LEVEL TWO - automation
        self.automate = Automaton('automate', self)

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
        # echo actions
        elif request in [ACTIONS.PREDICT, ACTIONS.SCORE]:
            return self.echo_request(self.predict, request, **kw)
        # notify handler
        elif request == ACTIONS.CHANGE_MODE:
            return self.echo_request(self.client, request, **kw)
        # swap mode
        elif request == EVENTS.MODE_FAILURE:
            self.echo_request(self.mediate, EVENTS.MODE_FAILURE)
            self.client.swap()
        # notify mediator
        elif request in MEDIATE_EVENTS:
            self.echo_request(self.mediate, request, **kw)
        # connection error
        elif request == EVENTS.CONNECTION_ERROR:
            self.echo_request(self.mediate, request)
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
