#!/usr/bin/env python

"""
forecaster.predict.mean_reversion
~~~~~~~~~~~~~~

Use a mean reversion for trading.
Use a strategy pattern to work with a yml file.
"""

import logging

import numpy as np
import pandas as pd
from scipy import stats

from forecaster.predict.utils import AverageTrueRange
from forecaster.utils import ACTIONS

logger = logging.getLogger('forecaster.predict.mean_reversion')


class MeanReversionPredicter(object):
    """predicter"""

    def __init__(self, strategy):
        self.mult = strategy['mult']
        logger.debug("initied MeanReversionPredicter")

    def predict(self, candles):
        """predict if is it worth"""
        # linear least-squared regression
        band = self.get_band(candles)
        close = [x['close'] for x in candles][-1]
        diff = close - band  # get diff to display
        perc = 100 * (close / band - 1)  # get diff to display
        if close > band:
            logger.debug("above bolliger band of %f - %.2f%%" % (diff, perc))
            return ACTIONS.SELL
        else:
            logger.debug("below bolliger band of %f - %.2f%%" % (diff, perc))
            return ACTIONS.BUY

    def get_band(self, candles):
        """get bolliger band"""
        day_closes = [x['close'] for x in candles]
        moving_average = stats.linregress(range(1, len(day_closes) + 1), day_closes)[1]
        moving_dev = AverageTrueRange(candles)  # deviation function
        band = moving_average + self.mult * moving_dev  # calculate Bolliger Band
        return band
