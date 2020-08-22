# ~~~~ bot.py ~~~~
#  forecaster.bot
# ~~~~~~~~~~~~~~~~

from forecaster.console import ForeCliConsole


def DEBUG(text):
    ForeCliConsole().debug(text, "exception")

def ERROR(text):
    ForeCliConsole().error(text, "exception")


class BotNotSetUp(Exception):
    def __init__(self):
        self.msg = "Bot need to be set up firts"
        ERROR(self.msg)
        super().__init__(self.msg)

class MarketClosed(Exception):
    def __init__(self):
        self.msg = "Market closed"
        DEBUG(self.msg)
        super().__init__(self.msg)