import sys
import time
from cryptotrader.bot import Bot

# logging
import logging
logger = logging.getLogger('cryptotrader.test')


def main():
    logging.getLogger('cryptotrader').setLevel(logging.DEBUG)
    bot = Bot()
    bot.view.tele.listen()
    logger.debug("bot launched")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.stderr.write('\r' + "exiting...\n")
        bot.view.tele.updater.stop()
        logger.debug("exited")


if __name__ == '__main__':
    main()
