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

logger = logging.getLogger('forecaster.predict')


class Predicter(object):
    """main predicter"""

    def __init__(self, strat):
        self.strategy = read_strategy(strat)['predicter']
        strategy = {'mult': self.strategy['multiplier']}
        self.MeanReversion = MeanReversionPredicter(strategy)
        logger.debug("Predicter initied")

    def predict(self, symbol, interval, timeframe):
        candles = Client().get_last_candles(symbol, interval, timeframe)
        prediction = self.MeanReversion.predict(candles)
        return prediction

    def check_position(self, position, candles):
        """predict bolliger band more accurate"""
        band = self.MeanReversion.get_band(candles)
        if position.mode == 'buy':
            if position.current_price >= band:
                return 'CLOSE_POS'
        elif position.mode == 'sell':
            if position.current_price <= band:
                return 'CLOSE_POS'
