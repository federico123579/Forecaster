#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os.path
import sys
import subprocess
from forecaster import Bot, config_bot
from forecaster.__version__ import __version__


def main():
    # PARSER
    parser = argparse.ArgumentParser(
        prog='forecaster', description="forecaster trading bot")
    parser.add_argument('--foreground', dest="foreground",
                        action="store_true", help="launch as a service")
    parser.add_argument('--config', dest="config",
                        action="store_true", help="start config mode")
    parser.add_argument('-v', '--verbose', action="count", default=0)
    parser.add_argument('-q', '--quiet', action="count", default=0)
    parser.add_argument('--version', action="version", version="%(prog)s {}".format(__version__))
    args = parser.parse_args()
    root_logger = logging.getLogger('forecaster')
    # - verbose
    if args.verbose >= 1:
        root_logger.setLevel(logging.DEBUG)
    elif args.quiet >= 1:
        root_logger.setLevel(logging.WARNING)
    # - config
    if args.config:
        try:
            config_bot()
        except KeyboardInterrupt:
            sys.stdout.write("\rexited...")
        finally:
            return
    if args.foreground:
        path = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), 'run.sh')
        subprocess.call(path)
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
