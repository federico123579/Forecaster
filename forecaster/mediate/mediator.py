"""
forecaster.mediate.mediator
~~~~~~~~~~~~~~

Proxy class to mediate between client and server.
"""

import logging
import os

from forecaster.enums import EVENTS
from forecaster.mediate.telegram import TelegramMediator
from forecaster.patterns import Chainer
from forecaster.utils import read_strategy

logger = logging.getLogger('forecaster.mediate')


class Mediator(Chainer):
    """main mediator"""

    def __init__(self, strat, bot=None):
        super().__init__(bot)
        self.strategy = read_strategy(strat)['mediator']
        token = os.environ['FORECASTER_TELEGRAM_TOKEN']
        self.Telegram = TelegramMediator(token, bot)
        logger.debug("MEDIATOR: ready")

    def handle_request(self, event, **kw):
        self.pass_request(event, **kw)

    def start(self):
        self.Telegram.activate()
        logger.debug("MEDIATOR: started")

    def stop(self):
        self.Telegram.deactivate()
        logger.debug("MEDIATOR: stopped")

    def need_conf(self):
        self.Telegram.config_needed()
        logger.warning("MEDIATOR: need config")
