#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

"""
forecaster.bot
~~~~~~~~~~~~~~

The bot.
"""

import sys
import time
from forecaster.core.controller import UltraController
from forecaster.automatism.automata import Automata

# logging
import logging
logger = logging.getLogger('forecaster')


class Bot(UltraController):
    def __init__(self):
        super().__init__()

    def start_automatism(self):  # OPTIMIZE
        self.auto = Automata(self)
        self.auto.start()

    def off(self):
        self.stop()
        self.auto.stop()


# main function
def main():
    logger.setLevel(logging.DEBUG)
    bot = Bot()
    bot.start()
    logger.debug("bot launched")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.stderr.write('\r' + "exiting...\n")
        bot.off()
        logger.debug("exited")


if __name__ == "__main__":
    main()
