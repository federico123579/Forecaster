#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import sys
import time
from forecaster.core.controller import UltraController

# logging
import logging
logger = logging.getLogger('forecaster')


class Bot(UltraController):
    def __init__(self):
        super().__init__()


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
        bot.stop()
        logger.debug("exited")


if __name__ == "__main__":
    main()
