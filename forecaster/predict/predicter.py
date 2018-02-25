#!/usr/bin/env python

"""
forecaster.predict.predicter
~~~~~~~~~~~~~~

Facade class to predict working with big data and NNs.
"""

import logging

from forecaster.handler import Client
from forecaster.predict.mean_reversion import MeanReversionPredicter
from forecaster.utils import read_strategy

logger = logging.getLogger('forecaster.predict.predicter')


class Predicter(object):
    """main predicter"""

    def __init__(self, strat):
        self.strategy = read_strategy(strat)['predicter']
        self.timeframe = self.strategy['timeframe']
        self.interval = self.strategy['count']
        self.MeanReversion = MeanReversionPredicter(self.strategy['multiplier'])
        logger.debug("predicter initied")

    def predict(self):
        closes = Client().get_last_closes('EURUSD', self.interval, self.timeframe)
        prediction = self.MeanReversion.predict(closes)
        logger.info(prediction)
