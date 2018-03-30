"""
forecaster.mediate.mediator
~~~~~~~~~~~~~~

Proxy class to mediate between client and server.
"""

import logging
import os
import signal

from forecaster.enums import EVENTS
from forecaster.exceptions import MissingData
from forecaster.mediate.telegram import TelegramMediator
from forecaster.patterns import Chainer
from forecaster.utils import read_tokens

LOGGER = logging.getLogger('forecaster.mediate')


class Mediator(Chainer):
    """Adapter and proxy for accessing telegram"""

    def __init__(self, bot=None):
        super().__init__(bot)
        token = read_tokens()['telegram']
        self.telegram = TelegramMediator(token, bot)
        LOGGER.debug("MEDIATOR: ready")

    def handle_request(self, event, **kw):
        """handle requests from chainers"""
        # raise missing data
        if event == EVENTS.MISSING_DATA:
            self.need_conf()
            raise MissingData()
        # log mode failure
        elif event == EVENTS.MODE_FAILURE:
            log_text = "Mode failed to login. Changing mode"
            LOGGER.warning(log_text)
            self.log(log_text)
        # notify telegram to close position
        elif event == EVENTS.CLOSED_POS:
            self.telegram.close_pos(kw['pos'].result)
        # notify telegram of market closed
        elif event == EVENTS.MARKET_CLOSED:
            self.log("Market closed for *{}*".format(kw['sym']))
        # connection error
        elif event == EVENTS.CONNECTION_ERROR:
            self.log("Connection error caught")
        else:
            self.pass_request(event, **kw)

    def start(self):
        """start listener"""
        self.telegram.activate()
        LOGGER.debug("MEDIATOR: started")

    def stop(self):
        """stop listener"""
        # self.telegram.deactivate()  # BUG
        os.kill(os.getpid(), signal.SIGINT)
        LOGGER.debug("MEDIATOR: stopped")

    def need_conf(self):
        """notify telegram"""
        self.telegram.config_needed()
        LOGGER.warning("MEDIATOR: need config")

    def idle(self):
        """idle telegram updater"""
        LOGGER.debug("idling...")
        self.telegram.updater.idle()

    def log(self, msg):
        """send msg"""
        self.telegram.send_msg(msg)
