#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
forecaster.bot
~~~~~~~~~~~~~~

The Bot Client class.
"""

import logging
import os
import time

from forecaster.automate import Automaton
from forecaster.enums import EVENTS
from forecaster.exceptions import *
from forecaster.handler import Client, SentryClient
from forecaster.mediate import Mediator
from forecaster.patterns import Chainer
from forecaster.predict import Predicter
from forecaster.utils import read_strategy

logger = logging.getLogger('forecaster.bot')


class Bot(Chainer):
    """main controller"""

    def __init__(self, strat='default'):
        super().__init__()
        self.strategy = read_strategy(strat)
        self._check_enironment()
        # LEVEL ZERO - access to apis and track errors
        self.sentry = SentryClient()
        self.client = Client(strat, self)
        self.mediate = Mediator(strat, self)
        # LEVEL ONE - algorithmic core
        self.predict = Predicter(strat)
        # LEVEL TWO - automation
        self.automate = Automaton(strat, self.predict, self.mediate, self)

    def _check_enironment(self):
        """check environment variables"""
        try:
            os.environ['FORECASTER_TELEGRAM_TOKEN']
            os.environ['FORECASTER_SENTRY_TOKEN']
        except KeyError:
            raise MissingToken()

    def handle_request(self, event, **kw):
        """handle requests from chainers"""
        if event == EVENTS.START_BOT:
            self.start_bot()
        elif event == EVENTS.STOP_BOT:
            self.stop_bot()
        elif event == EVENTS.MISSING_DATA:
            self.mediate.need_conf()
        elif event == EVENTS.CLOSED_POS:
            pos = kw['pos']
            self.mediate.Telegram.close_pos(pos.result)

    def start(self):
        """start cycle"""
        # first level: interface for receiving commands
        self.mediate.start()
        logger.debug("BOT: ready")

    def stop(self):
        self.automate.stop()
        self.mediate.stop()
        logger.debug("BOT: shutted down")

    def start_bot(self):
        """start bot cycle"""
        try:
            self.client.start()
            self.automate.start()
            break
        except MissingData as e:
            self.handle_request(EVENTS.MISSING_DATA)
        logger.debug("BOT: started")

    def stop_bot(self):
        self.automate.stop()
        logger.debug("BOT: stopped")


def main():
    try:
        logging.getLogger('forecaster').setLevel(logging.DEBUG)
        bot = Bot('default')
        bot.start()
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        logger.debug("exiting")
        bot.stop()
        logger.debug("exited")
    except Exception as e:
        logger.exception(e)
        raise


if __name__ == '__main__':
    main()
