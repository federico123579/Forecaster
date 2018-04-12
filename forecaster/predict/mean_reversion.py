"""
forecaster.predict.mean_reversion
~~~~~~~~~~~~~~

Use a mean reversion for trading.
Use a strategy pattern to work with a yml file.
"""

import logging

from scipy import stats

from forecaster.predict.utils import AverageTrueRange
from forecaster.enums import ACTIONS

LOGGER = logging.getLogger('forecaster.predict.mean_reversion')


class MeanReversionPredicter(object):
    """predicter"""

    def __init__(self, strategy):
        self.mult = strategy['mult']
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
            return ACTIONS.SELL
        else:
            LOGGER.debug("below bolliger band of {} - {:.2f}%".format(diff, perc))
            return ACTIONS.BUY

    def get_score(self, candles):
        """get score from band relative"""
        close = [x['close'] for x in candles][-1]
        band = self.get_band(candles)
        return abs(close - band) / close

    def get_band(self, candles):
        """get bolliger band"""
        day_closes = [x['close'] for x in candles]
        moving_average = stats.linregress(range(1, len(day_closes) + 1), day_closes)[1]
        moving_dev = AverageTrueRange(candles)  # deviation function
        band = moving_average + self.mult * moving_dev  # calculate Bolliger Band
        return band
