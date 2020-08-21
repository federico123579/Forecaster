# ~~~~ bot.py ~~~~
#  forecaster.bot
# ~~~~~~~~~~~~~~~~

from forecaster.console import ForeCliConsole


def ERROR(text):
    ForeCliConsole().error(text, "exception")


class BotNotSetUp(Exception):
    def __init__(self):
        self.msg = "Bot need to be set up firts"
        ERROR(msg)
        super().__init__(self.msg)