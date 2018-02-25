#!/usr/bin/env python

"""
forecaster.predict.predicter
~~~~~~~~~~~~~~

Facade class to predict working with big data and NNs.
"""

import logging

from forecaster.predict.mean_reversion import MeanReversionPredicter
from forecaster.utils import read_strategy

logger = logging.getLogger('forecaster.predict.predicter')


class Predicter(object):
    """main predicter"""

    def __init__(self, strat):
        self.strategy = read_strategy(strat)['predicter']
        self.MeanReversion = MeanReversionPredicter(self.strategy['multiplier'])
        logger.debug("predicter initied")

    def predict(self):
        pass
        # TODO: NEED OF HANDLER
