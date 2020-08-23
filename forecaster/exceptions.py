# ~~~~ bot.py ~~~~
#  forecaster.bot
# ~~~~~~~~~~~~~~~~

from datetime import datetime, timedelta

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
    def __init__(self, time_to_open):
        self.time_to_open = time_to_open
        open_datetime = datetime.now() + timedelta(seconds=time_to_open)
        date_format = f"{open_datetime.year}-{open_datetime.month:02d}-{open_datetime.day:02d}"
        time_format = f"{open_datetime.hour:02d}:{open_datetime.minute:02d}:{open_datetime.second:02d}"
        self.msg = (f"Market closed, reopen on {date_format} at {time_format}," +
                    f" in {time_to_open} seconds")
        DEBUG(self.msg)
        super().__init__(self.msg)