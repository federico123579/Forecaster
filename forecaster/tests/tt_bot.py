from forecaster.bot import Bot
import logging
from forecaster.handler import Client
from forecaster.predict.predicter import Predicter


def tst_bot():
    # BOT PROCESSES
    logging.getLogger('XTBApi').setLevel(logging.WARNING)
    bot = Bot('default')
    try:
        bot.start()
        bot.idle()
    except KeyboardInterrupt:
        bot.stop()
    except Exception as e:
        bot.sentry.captureException(e)
        raise


tst_bot()