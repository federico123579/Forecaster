"""
forecaster.predict.utils
~~~~~~~~~~~~~~

Various utils to predicter.
"""

import abc
from forecaster.enums import ACTIONS


# --[ ABSTRACTIATION ]--
class PhasesChecker(list):
    """implementation of phases checker"""

    def __init__(self, num_phases):
        super().__init__([False for x in range(int(num_phases))])

    def set(self, index):
        self.__setitem__(index, True)

    def clear(self):
        length = self.__len__()
        self.__init__([False for x in range(length)])

    def check(self, index):
        return self.__getitem__(index) is True

    def check_all(self):
        return all(x for x in self.__iter__())


class CandleStick(object):
    """implementation of candlestick"""

    def __init__(self, candle):
        self.open = candle['open']
        self.high = candle['high']
        self.low = candle['low']
        self.close = candle['close']
        self.body = abs(self.close - self.open)

    def calculate_direction(self):
        if self.close - self.open > 0:
            return 'up'
        elif self.close - self.open < 0:
            return 'down'
        else:
            return 'doji'


class Prediction(object):
    """abstract implementation of prediction encapsulation"""

    def __init__(self, action, score=0):
        self.action = action
        self.score = score


# --[ FUNCTIONS ]--
def average_true_range(candles):
    """calculates avergae true range"""
    candles = check_candles(candles)
    ATR = 0.0  # init ATR
    for candle in candles[1:]:
        ATR = (ATR * (len(candles) - 1) + (candle.high - candle.low)) / len(candles)
    return ATR


def calculate_trend(candles):
    """calculate trend"""
    candles = check_candles(candles)
    closes = [x.close for x in candles]
    first = closes[0]
    last = closes[-1]
    diff = last - first
    if diff >= 0:
        return 1
    else:
        return 0


def check_candles(candles):
    new_list = []
    for candle in candles:
        if not isinstance(candle, CandleStick):
            new_list.append(CandleStick(candle))
        else:
            new_list.append(candle)
    return new_list
