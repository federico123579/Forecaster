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
from forecaster.enums import EVENTS
from forecaster.handler import Client, SentryClient
from forecaster.mediate import Mediator
from forecaster.patterns import Chainer
from forecaster.predict import Predicter
from forecaster.utils import read_strategy

LOGGER = logging.getLogger('forecaster.bot')


class Bot(Chainer):
    """Mediator for every component and head of chaining of resposabilities"""

    def __init__(self, strat='default'):
        super().__init__()
        self.strategy = read_strategy(strat)
        # LEVEL ZERO - access to apis and track errors
        self.sentry = SentryClient()
        self.client = Client(self)
        self.mediate = Mediator(strat, self)
        # LEVEL ONE - algorithmic core
        self.predict = Predicter('pred')
        # LEVEL TWO - automation
        self.automate = Automaton(strat, self.predict, self.mediate, self)

    def handle_request(self, event, **kw):
        """handle requests from chainers"""
        if event == EVENTS.START_BOT:
            self.start_bot()
        elif event == EVENTS.STOP_BOT:
            self.stop_bot()
        elif event == EVENTS.SHUTDOWN:
            self.stop()
        elif event == EVENTS.MISSING_DATA:
            self.mediate.need_conf()
        elif event == EVENTS.MODE_FAILURE:
            log_text = "Mode {} failed to login. Changing mode".format(self.client.mode)
            LOGGER.warning(log_text)
            self.mediate.log(log_text)
            self.client.swap()
        elif event == EVENTS.CLOSED_POS:
            pos = kw['pos']
            self.mediate.telegram.close_pos(pos.result)
        elif event == EVENTS.MARKET_CLOSED:
            self.mediate.log("Market closed for *{}*".format(kw['sym']))
        elif event == EVENTS.CHANGE_MODE:
            mode = kw['mode']
            Client().handle_request(event, mode=mode)

    def start(self):
        """start cycle"""
        # first level: interface for receiving commands
        self.mediate.start()
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
        self.client.start()
        self.automate.start()
        LOGGER.debug("BOT: started")

    def stop_bot(self):
        self.automate.stop()
        LOGGER.debug("BOT: stopped")
