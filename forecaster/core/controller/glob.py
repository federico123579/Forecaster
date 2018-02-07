# -*- coding: utf-8 -*-

"""
forecaster.core.controller.glob
~~~~~~~~~~~~~~

This module provides glob access.
"""

from forecaster.patterns import Subject
from forecaster.glob import Collector

# logging
import logging
logger = logging.getLogger('forecaster.controller.glob')


# define a singleton for strategy behavior pattern
class OmniController(Collector):
    """controller singleton for strategy purpose"""
    def __init__(self):
        super().__init__()
        self.mount('PERS_DATA')
        self.pers_data = self.collection['PERS_DATA'].config


# define a default controller
class DefaultController(Subject):
    def __init__(self, supervisor):
        super().__init__()
        self.attach(supervisor)
