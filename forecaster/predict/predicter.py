#!/usr/bin/env python

"""
forecaster.predict.predicter
~~~~~~~~~~~~~~

Facade class to predict working with algorithms.
"""

import logging

from forecaster.enums import ACTIONS
from forecaster.handler import Client
from forecaster.patterns import Chainer
from forecaster.predict.mean_reversion import MeanReversionPredicter
from forecaster.utils import read_strategy

LOGGER = logging.getLogger('forecaster.predict')


class Predicter(Chainer):
    """Adapter proxy class to interface with predictive algorithms"""

    def __init__(self, strat, bot=None):
        super().__init__(bot)
        self.strategy = read_strategy(strat)
        strategy = {'mult': self.strategy['multiplier']}
        self.MeanReversion = MeanReversionPredicter(strategy)
        LOGGER.debug("Predicter initied")

    def handle_request(self, request, **kw):
        """handle requests from chainers"""
        # predict
        if request == ACTIONS.PREDICT:
            return self.predict.predict(*kw['args'])
        else:
            self.pass_request(request, **kw)

    def predict(self, symbol, interval, timeframe):
        candles = Client().get_last_candles(symbol, interval, timeframe)
        prediction = self.MeanReversion.predict(candles)
        return prediction
