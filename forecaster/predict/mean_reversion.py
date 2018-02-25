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

logger = logging.getLogger('forecaster.predict.mean_reversion')


class MeanReversionPredicter(object):
    """predicter"""

    def __init__(self, multiplier):
        self.mult = multiplier
        logger.debug("initied MeanReversionPredicter")

    def predict(self, day_closes):
        """predict if is it worth"""
        # linear least-squared regression
        moving_average = stats.linregress(range(1, len(day_closes)+1), day_closes)[1]
        moving_dev = np.std(day_closes)  # standard deviation
        band = moving_average + self.mult * moving_dev  # calculate Bolliger Band
        close = day_closes[-1]
        if close > band:
            logger.debug("above bolliger band")
            return 'sell'
        else:
            logger.debug("below bolliger band")
            return 'buy'
