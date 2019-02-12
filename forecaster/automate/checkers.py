"""
forecaster.automate.checker
~~~~~~~~~~~~~~

Contains all position checkers, check when close a position.
Every Checker is evalued with a complexity_level that define the level of
complexity of operations.
"""

import abc
import logging
import time
from threading import Event

from forecaster.automate.utils import ACTIONS, LogThread, ThreadHandler, wait_precisely
from forecaster.enums import TIMEFRAME
from forecaster.handler import Client
from forecaster.patterns import Chainer
from forecaster.predict.utils import AverageTrueRange

LOGGER = logging.getLogger('forecaster.automate.checker')


# Abstract class for defining new Checkers
class PositionChecker(Chainer, metaclass=abc.ABCMeta):
    """abstract implementation class for checkers"""

    def __init__(self, sleep_time, successor):
        super().__init__(successor)
        self.sleep_time = sleep_time
        self.active = Event()
        LOGGER.debug("{!s} initied".format(self.__class__.__name__))

    def handle_request(self, event, **kw):
        """handle requests from chainers"""
        self.pass_request(event, **kw)

    @abc.abstractmethod
    def check(self, *args):
        """main check function"""
        pass

    def run(self):
        """run method for threading"""
        while self.active.is_set():
            start = time.time()  # record timing
            try:
                for pos in Client().positions:
                    Client().refresh()  # refresh and update
                    action = self.check(pos)
                    if action is not None:
                        self.handle_request(action, pos=pos, checker=self.__class__.__name__)
            except Exception as e:
                LOGGER.error("Caught exception in checker {}".format(self.__class__.__name__))
                LOGGER.error(e)
                LOGGER.error("continuing in 10 seconds...")
                time.sleep(10)
                continue
            wait_precisely(self.sleep_time, start, self.active)  # wait and repeat

    def start(self):
        """start the thread"""
        self.active.set()
        ThreadHandler().add_event(self.active)
        thread = LogThread(target=self.run)
        thread.start()
        ThreadHandler().add_thread(thread)
        LOGGER.debug("{!s} started".format(self.__class__.__name__))

    def stop(self):
        """stop the thread"""
        self.active.clear()
        LOGGER.debug("{!s} stopped".format(self.__class__.__name__))


class PositionTotalChecker(PositionChecker):
    """abstract implementation for total checker"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self):
        """alternative run method"""
        while self.active.is_set():
            start = time.time()  # record timing
            Client().refresh()  # refresh and update
            action = self.check(Client().positions)
            if action is not None:
                self.handle_request(action, checker=self.__class__.__name__)
            wait_precisely(self.sleep_time, start, self.active)  # wait and repeat


# +----------------------------------------------------------------------+
# | complexity_level: 2                                                  |
# | calculate ATR, then check diff with the price of position opening    |
# | and the current price, if current price cross the percentage limit   |
# | send request ACTIONS.CLOSE else ACTIONS.KEEP                         |
# +----------------------------------------------------------------------+
class RelativeChecker(PositionChecker):
    """Check Average True Range and put limits on percentages of the range"""

    def __init__(self, strat, positioner):
        super().__init__(strat['sleep'], positioner)
        self.gain = strat['gain']
        self.loss = strat['loss']
        self.avg = strat['avg']

    def check(self, position):
        pos_price = position.price
        curr_price = position.current_price
        candles = Client().get_last_candles(
            position.instrument, self.avg['count'], self.avg['timeframe'])
        ATR = AverageTrueRange(candles)
        diff = pos_price - ATR
        fav_price = pos_price + diff * self.gain
        unfav_price = pos_price - diff * self.loss
        # closer to 1 cross the limit, as it goes down the loss increases
        progress = -(fav_price - curr_price) / (fav_price - pos_price) + 1
        unprogress = -(unfav_price - curr_price) / (unfav_price - pos_price) + 1
        LOGGER.debug("progress to profit {:.2f}%".format(100 * progress))
        LOGGER.debug("progress to loss {:.2f}%".format(100 * unprogress))
        if progress >= 1 or unprogress >= 1:
            return ACTIONS.CLOSE
        else:
            return ACTIONS.KEEP


# +----------------------------------------------------------------------+
# | complexity_level: 1                                                  |
# | Check if profit exceeded limits fixed limits                         |
# +----------------------------------------------------------------------+
class ReversionChecker(PositionChecker):
    def __init__(self, strat, positioner):
        super().__init__(strat['sleep'], positioner)
        self.Meanrev = positioner.predicter.MeanReversion
        self.count = int(TIMEFRAME[positioner.auto_strategy['timeframe']] /
                         TIMEFRAME[strat['timeframe']]) * positioner.auto_strategy['count']
        self.timeframe = strat['timeframe']

    def check(self, position):
        candles = Client().get_last_candles(position.instrument, self.count, self.timeframe)
        band = self.Meanrev.get_band(candles)
        if position.mode == 'buy' and position.current_price >= band:
            LOGGER.debug("overtaken band")
            return ACTIONS.CLOSE
        elif position.mode == 'sell' and position.current_price <= band:
            LOGGER.debug("overtaken band")
            return ACTIONS.CLOSE


# +----------------------------------------------------------------------+
# | complexity_level: 1                                                  |
# | Check if profit reached a fixed value                                |
# +----------------------------------------------------------------------+
class FixedTotalChecker(PositionTotalChecker):
    def __init__(self, strat, positioner):
        super().__init__(strat['sleep'], positioner)
        self.gain = strat['gain']
        self.loss = strat['loss']

    def check(self, positions):
        total_profit = sum([pos.result for pos in positions])
        close = False
        if self.gain is not None:
            if total_profit >= self.gain:
                close = True
        if self.loss is not None:
            if total_profit <= -self.loss:
                close = True
        if close is True:
            LOGGER.debug("CLOSING: total profit {:.2f}".format(total_profit))
            return ACTIONS.CLOSE_ALL
        LOGGER.debug("total profit {:.2f}".format(total_profit))


# +----------------------------------------------------------------------+
# | complexity_level: 1                                                  |
# | Check if profit reached a fixed value                                |
# +----------------------------------------------------------------------+
class RelativeTotalChecker(PositionTotalChecker):
    def __init__(self, strat, positioner):
        super().__init__(strat['sleep'], positioner)
        self.gain = strat['gain']
        self.loss = strat['loss']

    def check(self, positions):
        total_profit = sum([pos.result for pos in positions]) / len(positions)
        close = False
        if self.gain is not None:
            if total_profit >= self.gain:
                close = True
        if self.loss is not None:
            if total_profit <= -self.loss:
                close = True
        if close is True:
            LOGGER.debug("CLOSING: total profit {:.2f}".format(total_profit))
            return ACTIONS.CLOSE_ALL
        LOGGER.debug("total profit {:.2f}".format(total_profit))


# +----------------------------------------------------------------------+
# | complexity_level: 1                                                  |
# | Check if profit exceeded fixed limits                                |
# +----------------------------------------------------------------------+
class FixedChecker(PositionChecker):
    def __init__(self, strat, positioner):
        super().__init__(strat['sleep'], positioner)
        self.gain = strat['gain']
        self.loss = -strat['loss']

    def check(self, position):
        profit = position.result
        close = False
        if self.gain is not None:
            if profit >= self.gain:
                close = True
        if self.loss is not None:
            if profit <= self.loss:
                close = True
        if close is True:
            LOGGER.debug("position profit {:.2f}".format(profit))
            return ACTIONS.CLOSE


# factory class
FactoryChecker = {
    'relative': RelativeChecker,
    'reversion': ReversionChecker,
    'fixed': FixedChecker,
    'totalfixed': FixedTotalChecker,
    'totalrelative': RelativeTotalChecker}
