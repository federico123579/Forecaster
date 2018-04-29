"""
forecaster.predict.algorithms
~~~~~~~~~~~~~~

Algorithms for trading.
Use a strategy pattern to work with a yml file.
"""

import abc
import logging

from forecaster.enums import ACTIONS
from forecaster.predict import utils
from forecaster.utils import read_strategy
from scipy import stats

LOGGER = logging.getLogger('forecaster.predict.algorithms')


class AbstractPredicter(metaclass=abc.ABCMeta):
    """abstract implementation of predicter"""

    def __init__(self, algo_name=None):
        self.name = algo_name
        self.scores = {}
        # try:
        self.strategy = read_strategy(algo_name, ['algos'])
        # except FileNotFoundError:
        #     pass

    def get_weight(self):
        """lazy implementation"""
        if not hasattr(self, 'algo_weight'):
            self.algo_weight = read_strategy('predicter')['weights'][self.name]
        return self.algo_weight

    @abc.abstractmethod
    def predict(self, candles):
        pass

    @abc.abstractmethod
    def get_score(self, candles):
        pass


# -[ CANDLESTICK PATTERN PREDICTIONS ]-
class AbstractCandlestickPredicter(AbstractPredicter, metaclass=abc.ABCMeta):
    """abstract implementation of predicter"""

    def __init__(self, num_phases, algo_name):
        super().__init__(algo_name)
        self.phases = utils.PhasesChecker(num_phases)
        self.candles = []

    def _set_candle_index(self, candle):
        if candle not in self.candles:
            raise ValueError("{} not in self.candles".format(candle))
        self._candle_index = self.candles.index(candle)


# +----------------------------------------------------------------------+
# | complexity_level: 1                                                  |
# | category: candlestick algorithms                                     |
# | Predict using the three stars in the south candlestick pattern       |
# +----------------------------------------------------------------------+
class ThreeStarsInTheSouthPredicter(AbstractCandlestickPredicter):
    """Use the bullish three line strike pattern - 84% acc."""

    def __init__(self, algo_name):
        super().__init__(4, algo_name)
        self.candles_history = int(self.strategy['candles-history'])

    def predict(self, candles):
        """predict if is it worth"""
        candles = candles[-self.candles_history:]
        if self._check(candles):
            score = self.get_score()
            return utils.Prediction(ACTIONS.BUY, score)
        else:
            return utils.Prediction(ACTIONS.DISCARD)

    def _check(self, candles):
        """check all phases in candles"""
        self.candles = [utils.CandleStick(x) for x in candles]
        self._check_first()
        self._check_second()
        self._check_third()
        self._check_fourth()
        # check all conditions in phases
        return self.phases.check_all()

    def _check_first(self):
        """if the market is in a downtrend"""
        # CONDITION
        trend = utils.calculate_trend(self.candles)
        if trend == 0:  # if downtrend
            self.phases.set(0)

    def _check_second(self):
        """if the first candle is black with a long real body,
        long lower shadow, and no upper shadow"""
        # CHECK PREVIOUS
        if not self.phases.check(0):
            return  # abort
        # CONDITION
        for candle in self.candles:  # check every candle for pattern recognition
            if (candle.calculate_direction() == 'down' and  # direction  down
                    candle.body > candle.close - candle.low and  # real body higher than shadow
                    candle.high == candle.open):  # no higher shadow body
                self.phases.set(1)
                self._set_candle_index(candle)  # set index for the following
                return
        # ABORT
        self.phases.clear()

    def _check_third(self):
        """if the second candle is black with a shorter real body
        and a higher low than the first candle’s low"""
        # CHECK PREVIOUS
        if not self.phases.check(1):
            return  # abort
        # CONDITION
        prev_candle = self.candles[self._candle_index]
        try:  # try to get second candle
            candle = self.candles[self._candle_index+1]
        except IndexError:  # ABORT
            self.phases.clear()
            return
        if (candle.calculate_direction() == 'down' and  # direction down
                candle.body < prev_candle.body and  # body lower than previous
                candle.low > prev_candle.low):  # higher low than previous
            self.phases.set(2)
            self._set_candle_index(candle)  # set index for the following
        else:  # ABORT
            self.phases.clear()

    def _check_fourth(self):
        """if the third candle is black with a short real body
        and no shadows and a close that’s within the hi-lo range of the second candle"""
        # CHECK PREVIOUS
        if not self.phases.check(2):
            return  # abort
        # CONDITION
        prev_candle = self.candles[self._candle_index]
        try:  # try to get second candle
            candle = self.candles[self._candle_index+1]
        except IndexError:  # abort
            self.phases.clear()
            return
        if (candle.calculate_direction() == 'down' and  # direction down
                candle.body < prev_candle.body and  # body lower than previous
                candle.low == candle.close and  # no shadow body
                candle.high == candle.open and
                # body between hi-lo range
                prev_candle.high < candle.close < prev_candle.low):
            self.phases.set(3)
            self._set_candle_index(candle)  # set index for score
        else:  # ABORT
            self.phases.clear()

    def get_score(self):
        """get score from band relative"""
        return (self._candle_index + 1) / len(self.candles)


# -[ ALGORITHM PATTERNS ]-
# +----------------------------------------------------------------------+
# | complexity_level: 1                                                  |
# | Predict using simple MeanReversion                                   |
# +----------------------------------------------------------------------+
class MeanReversionPredicter(AbstractPredicter):
    """predicter"""

    def __init__(self, algo_name):
        super().__init__(algo_name)
        self.mult = self.strategy['multiplier']
        LOGGER.debug("initied MeanReversionPredicter")

    def predict(self, candles):
        """predict if is it worth"""
        # linear least-squared regression
        band = self.get_band(candles)
        close = [x['close'] for x in candles][-1]
        diff = close - band  # get diff to display
        perc = 100 * (close / band - 1)  # get diff to display
        if close > band:
            LOGGER.debug("above bolliger band of {} - {:.2f}%".format(diff, perc))
            return utils.Prediction(ACTIONS.SELL, self.get_score(candles))
        else:
            LOGGER.debug("below bolliger band of {} - {:.2f}%".format(diff, perc))
            return utils.Prediction(ACTIONS.BUY, self.get_score(candles))

    def get_score(self, candles):
        """get score from band relative"""
        close = [x['close'] for x in candles][-1]
        band = self.get_band(candles)
        return abs(close - band) / close

    def get_band(self, candles):
        """get bolliger band"""
        day_closes = [x['close'] for x in candles]
        moving_average = stats.linregress(range(1, len(day_closes) + 1), day_closes)[1]
        moving_dev = utils.average_true_range(candles)  # deviation function
        band = moving_average + self.mult * moving_dev  # calculate Bolliger Band
        return band
