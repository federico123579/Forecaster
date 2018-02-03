# -*- coding: utf-8 -*-

"""
forecaster.controller.glob
~~~~~~~~~~~~~~

This module provides glob access.
"""

from threading import Event
from forecaster.patterns import Subject
from forecaster.glob import Collector

# constants
UPDATE_PRICES_TIME = 2*60
UPDATE_VALUES_TIME = 60*60


# define a singleton for strategy behavior pattern
class OmniModel(Collector):
    """controller singleton for strategy purpose"""
    def __init__(self):
        super().__init__()
        self.mount('PERS_DATA')
        self.update()
        self.events = {'UPDATE': Event()}

    def update(self):
        for key in self.collection.keys():
            self.collection[key].read()
        self.pers_data = self.collection['PERS_DATA'].config


# define a default model
class DefaultModel(Subject):
    def __init__(self, supervisor):
        super().__init__()
        self.attach(supervisor)
