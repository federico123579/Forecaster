# -*- coding: utf-8 -*-

"""
bitgen.model.main
~~~~~~~~~~~~~~

This module provides the main model component of the pattern MVC.
"""

from bitgen.patterns import Subject, Observer
from bitgen.model.forex import ForexPredict

# logging
import logging
logger = logging.getLogger('bitgen.model')


# define a general controller
class Model(Subject, Observer):
    """control all controllers"""
    def __init__(self):
        super().__init__()
        self.forex = ForexPredict(self)

    def start(self):
        try:
            self.forex.init_creds()
        except MissingConfig:
            self.notify_observers('config')