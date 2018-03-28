from forecaster.mediate.telegram import TelegramMediator
from forecaster.utils import get_conf
from raven import Client


def test_validate_tokens():
    """validate tokens"""
    config = get_conf()
    telegram = config['TOKENS']['telegram']
    sentry = config['TOKENS']['sentry']
    bot = TelegramMediator(telegram, None)
    bot.bot.getMe()
    Client(dsn=sentry)
