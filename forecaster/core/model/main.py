# -*- coding: utf-8 -*-

"""
forecaster.model.main
~~~~~~~~~~~~~~

This module provides the main model component of the pattern MVC.
"""

from forecaster.glob import CURR
from forecaster.patterns import Subject, Observer
from forecaster.core.model.forex import ForexPredict
from forecaster.core.model.train import train
from forecaster.exceptions import *
from forecaster.core.model.exceptions import *

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
            self.forex.init_model()
        except MissingModel:
            train()
            self.forex.init_model()

    def pred_all(self):
        logger.debug("predicting")
        predictions = {}
        for curr in CURR:
            predictions[curr] = self.forex.predict(curr)
        logger.debug("predicted all currencies")
        return predictions

    # handle all events
    def notify(self, observable, event, **kwargs):
        logger.debug("Model notified - %s" % event)
        self.notify_observers(event, **kwargs)
