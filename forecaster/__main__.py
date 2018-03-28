#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os.path
import subprocess

from forecaster import Bot
from forecaster.utils import CLIConfig
from forecaster.__version__ import __version__


def main():
    # PARSER
    parser = argparse.ArgumentParser(
        prog='forecaster', description="forecaster trading bot")
    parser.add_argument('-v', '--verbose', action="count", default=0)
    parser.add_argument('-q', '--quiet', action="count", default=0)
    parser.add_argument('--foreground', dest="foreground",
                        action="store_true", help="launch as a service")
    parser.add_argument('--config', dest="config",
                        action="store_true", help="start config mode")
    parser.add_argument('--config-credentials', dest="config_creds",
                        action="store_true", help="config credentials from terminal")
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
        conf = CLIConfig('tokens', 'config', 'ini', True)
        conf.add_query_insert(('TOKENS', 'telegram'), 'telegram secret token')
        conf.add_query_insert(('TOKENS', 'sentry'), 'sentry secret token')
        conf.run()
        return
    if args.config_creds:
        conf = CLIConfig('credentials', 'data', 'json', True)
        conf.add_query_insert('username', 'username')
        conf.add_query_insert('password', 'password')
        conf.run()
        return
    if args.foreground:
        path = os.path.join(os.path.dirname(__file__), 'run.sh')
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
