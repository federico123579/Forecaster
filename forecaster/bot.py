#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
forecaster.bot
~~~~~~~~~~~~~~

The Bot Client class.
"""

import logging
import sys

from forecaster.automate import Automaton
from forecaster.automate.utils import ThreadHandler
from forecaster.enums import EVENTS
from forecaster.exceptions import MissingData
from forecaster.handler import Client, SentryClient
from forecaster.mediate import Mediator
from forecaster.patterns import Chainer
from forecaster.predict import Predicter
from forecaster.utils import CLI, get_conf, read_strategy, save_conf

logger = logging.getLogger('forecaster.bot')


class Bot(Chainer):
    """main controller"""

    def __init__(self, strat='default'):
        super().__init__()
        self.strategy = read_strategy(strat)
        # LEVEL ZERO - access to apis and track errors
        self.sentry = SentryClient()
        self.client = Client(strat, self)
        self.mediate = Mediator(strat, self)
        # LEVEL ONE - algorithmic core
        self.predict = Predicter(strat)
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
            sys.exit()  # exit from process
        elif event == EVENTS.MISSING_DATA:
            self.mediate.need_conf()
        elif event == EVENTS.CLOSED_POS:
            pos = kw['pos']
            self.mediate.Telegram.close_pos(pos.result)
        elif event == EVENTS.CHANGE_MODE:
            mode = kw['mode']
            Client().handle_request(event, mode=mode)

    def start(self):
        """start cycle"""
        # first level: interface for receiving commands
        self.mediate.start()
        logger.debug("BOT: ready")

    def stop(self):
        self.automate.stop()
        self.mediate.stop()
        ThreadHandler().stop_all()
        logger.debug("BOT: shutted down")

    def idle(self):
        logger.debug("BOT: idling")
        self.mediate.idle()

    def start_bot(self):
        """start bot cycle"""
        try:
            self.client.start()
            self.automate.start()
        except MissingData:
            self.handle_request(EVENTS.MISSING_DATA)
        logger.debug("BOT: started")

    def stop_bot(self):
        self.automate.stop()
        logger.debug("BOT: stopped")


def config_bot():
    CLI.print_bold("forecaster CONFIG mode enabled:")
    telegram_token = input(CLI.colored("please insert your telegram secret token:\n", 'yellow'))
    sentry_token = input(CLI.colored("please insert your sentry secret token:\n", 'yellow'))
    config = get_conf()
    config.set('TOKENS', 'telegram', telegram_token)
    config.set('TOKENS', 'sentry', sentry_token)
    save_conf(config)
    logger.info("config saved")
