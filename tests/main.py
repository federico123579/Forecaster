import logging
import time

from forecaster import Bot

logger = logging.getLogger('forecaster.tests')


def main():
    try:
        logging.getLogger('forecaster').setLevel(logging.DEBUG)
        bot = Bot('mean_rev')
        bot.start()
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        logger.debug("exiting")
        bot.stop()
        logger.debug("exited")
    except Exception as e:
        logger.exception(e)
        raise


if __name__ == '__main__':
    main()
