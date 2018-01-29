# -*- coding: utf-8 -*-

"""
forecaster.model.main
~~~~~~~~~~~~~~

This module provides the main model component of the pattern MVC.
"""

from forecaster.patterns import Subject, Observer
from forecaster.model.forex import ForexPredict
from forecaster.model.train import train
from forecaster.exceptions import *
from forecaster.model.exceptions import *

# logging
import logging
logger = logging.getLogger('forecaster.model')


# define a general controller
class Model(Subject, Observer):
    """control all controllers"""
    def __init__(self):
        super().__init__()
        self.times = [10, 2]
        self.forex = ForexPredict(self)

    def start(self):
        try:
            self.forex.init_creds()
            for t in self.times:
                self.forex.init_model(t)
        except MissingConfig:
            self.notify_observers('config')
        except MissingModel:
            for t in self.times:
                train(t, t)
                self.forex.init_model(t)

    def pred_all(self):
        logger.debug("predicting")
        predictions = {}
        for t in self.times:
            predictions[str(t)] = {}
            for curr in ['EURUSD', 'USDCHF', 'GBPUSD', 'USDJPY', 'USDCAD']:
                predictions[str(t)][curr] = self.forex.predict(curr, t)
        logger.debug("predicted all currencies")
        return predictions
