"""
forecaster.mediate.mediator
~~~~~~~~~~~~~~

Proxy class to mediate between client and server.
"""

import logging
import os
import signal

from forecaster.mediate.telegram import TelegramMediator
from forecaster.patterns import Chainer
from forecaster.utils import read_strategy, read_tokens

logger = logging.getLogger('forecaster.mediate')


class Mediator(Chainer):
    """main mediator"""

    def __init__(self, strat, bot=None):
        super().__init__(bot)
        self.strategy = read_strategy(strat)['mediator']
        token = read_tokens()['telegram']
        self.telegram = TelegramMediator(token, bot)
        logger.debug("MEDIATOR: ready")

    def handle_request(self, event, **kw):
        self.pass_request(event, **kw)

    def start(self):
        self.telegram.activate()
        logger.debug("MEDIATOR: started")

    def stop(self):
        # self.telegram.deactivate()  # BUG
        os.kill(os.getpid(), signal.SIGINT)
        logger.debug("MEDIATOR: stopped")

    def need_conf(self):
        self.telegram.config_needed()
        logger.warning("MEDIATOR: need config")

    def idle(self):
        logger.debug("idling...")
        self.telegram.updater.idle()
