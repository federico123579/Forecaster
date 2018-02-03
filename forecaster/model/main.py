# -*- coding: utf-8 -*-

"""
forecaster.model.main
~~~~~~~~~~~~~~

This module provides the main model component of the pattern MVC.
"""

from forecaster.glob import CURR
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
        self.forex = ForexPredict(self)

    def start(self):
        try:
            self.forex.init_creds()
            self.forex.init_model(10)
        except MissingConfig:
            self.notify_observers('config')
        except MissingModel:
            train(10)
            self.forex.init_model(10)

    def pred_all(self):
        logger.debug("predicting")
        predictions = {}
        for curr in CURR:
            predictions[curr] = self.forex.predict(curr, 10)
        logger.debug("predicted all currencies")
        return predictions
