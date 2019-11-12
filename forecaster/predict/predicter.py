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
        # EDITED IN ALPHA2
        super().__init__(bot)
        self.strategy = read_strategy(strat)
        self.MeanReversion = MeanReversionPredicter(self.strategy)
        LOGGER.debug("Predicter initied")

    def handle_request(self, request, **kw):
        """handle requests from chainers"""
        # predict
        if request == ACTIONS.PREDICT:
            return self.predict(*kw['args'])
        elif request == ACTIONS.SCORE:
            return self.get_score(*kw['args'])
        else:
            self.pass_request(request, **kw)

    def predict(self, symbol, timeframe, interval):
        candles = Client().get_last_candles(symbol, timeframe, interval)
        values = self.MeanReversion.predict(candles)
        price = Client().api.get_symbol(symbol)['bid']
        if price < values.iloc[-1]['BollBands_down']:
            return ACTIONS.BUY
        elif price > values.iloc[-1]['BollBands_up']:
            return ACTIONS.SELL

    def get_score(self, symbol, interval, timeframe):
        candles = Client().get_last_candles(symbol, interval, timeframe)
        score = self.MeanReversion.get_score(candles)
        return score
