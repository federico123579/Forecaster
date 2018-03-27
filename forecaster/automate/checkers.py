"""
forecaster.automate.checker
~~~~~~~~~~~~~~

Contains all position checkers.
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

logger = logging.getLogger('forecaster.automate.checker')


# Abstract class for defining new Checkers
class PositionChecker(Chainer, metaclass=abc.ABCMeta):
    """abstract class for checkers"""

    def __init__(self, sleep_time, successor):
        super().__init__(successor)
        self.sleep_time = sleep_time
        self.active = Event()
        logger.debug("{!s} initied".format(self.__class__.__name__))

    def handle_request(self, event, **kw):
        self.pass_request(event, **kw)

    @abc.abstractmethod
    def check(self, *args):
        pass

    # main loop
    def run(self):
        while self.active.is_set():
            start = time.time()  # record timing
            for pos in Client().api.account.positions:
                Client().refresh()  # refresh and update
                action = self.check(pos)
                if action is not None:
                    self.handle_request(ACTIONS[action], pos=pos)
            wait_precisely(self.sleep_time, start, self.active)  # wait and repeat

    def start(self):
        self.active.set()
        ThreadHandler().add_event(self.active)
        thread = LogThread(target=self.run)
        thread.start()
        ThreadHandler().add_thread(thread)
        logger.debug("{!s} started".format(self.__class__.__name__))

    def stop(self):
        self.active.clear()
        logger.debug("{!s} stopped".format(self.__class__.__name__))


# +----------------------------------------------------------------------+
# | complexity_level: 2                                                  |
# | calculate ATR, then check diff with the price of position opening    |
# | and the current price, if current price cross the percentage limit   |
# | send request 'CLOSE' else 'KEEP'                                     |
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
        logger.debug("progress to profit {:.2f}%%".format(100 * progress))
        logger.debug("progress to loss {:.2f}%%".format(100 * unprogress))
        if progress >= 1 or unprogress >= 1:
            return 'CLOSE'
        else:
            return 'KEEP'


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
            logger.debug("overtaken band")
            return 'CLOSE'
        elif position.mode == 'sell' and position.current_price <= band:
            logger.debug("overtaken band")
            return 'CLOSE'


# +----------------------------------------------------------------------+
# | complexity_level: 1                                                  |
# | Check if profit exceeded limits fixed limits                         |
# +----------------------------------------------------------------------+
class FixedChecker(PositionChecker):
    def __init__(self, strat, positioner):
        super().__init__(strat['sleep'], positioner)
        self.gain = strat['gain']
        self.loss = strat['loss']

    def check(self, position):
        profit = position.result
        if profit >= self.gain or profit <= self.loss:
            logger.debug("position profit {:.2f}".format(profit))
            return 'CLOSE'


# factory class
FactoryChecker = {
    'relative': RelativeChecker,
    'reversion': ReversionChecker,
    'fixed': FixedChecker}
