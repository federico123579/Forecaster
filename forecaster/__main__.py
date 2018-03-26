#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging

from forecaster import Bot, config_bot
from forecaster.__version__ import __version__


def main():
    # PARSER
    parser = argparse.ArgumentParser(
        prog='forecaster', description="forecaster trading bot")
    parser.add_argument('--config', dest="config",
                        action="store_true", help="start config mode")
    parser.add_argument('-v', '--verbose', action="count")
    parser.add_argument('--version', action="version", version="%(prog)s 2.0")
    args = parser.parse_args()
    root_logger = logging.getLogger('forecaster')
    # - verbose
    if args['verbose'] == 1:
        root_logger.setLevel(logging.INFO)
    elif args['verbose'] > 1:
        root_logger.setLevel(logging.DEBUG)
    # - config
    if args['config']:
        config_bot()
        return
    # BOT PROCESSES
    bot = Bot('default')
    try:
        bot.start()
        bot.idle()
    except KeyboardInterrupt:
        bot.stop()
    except Exception as e:
        bot.sentry.captureException(e)
        raise


if __name__ == '__main__':
    main()
