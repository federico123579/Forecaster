#!/usr/bin/env python

"""
forecaster.predict.predicter
~~~~~~~~~~~~~~

Facade class to predict working with algorithms.
"""

import logging

from forecaster.handler import Client
from forecaster.predict.mean_reversion import MeanReversionPredicter
from forecaster.utils import read_strategy

LOGGER = logging.getLogger('forecaster.predict')


class Predicter(object):
    """Adapter proxy class to interface with predictive algorithms"""

    def __init__(self, strat):
        self.strategy = read_strategy(strat)
        strategy = {'mult': self.strategy['multiplier']}
        self.MeanReversion = MeanReversionPredicter(strategy)
        LOGGER.debug("Predicter initied")

    def predict(self, symbol, interval, timeframe):
        candles = Client().get_last_candles(symbol, interval, timeframe)
        prediction = self.MeanReversion.predict(candles)
        return prediction
