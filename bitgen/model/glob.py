# -*- coding: utf-8 -*-

"""
bitgen.controller.glob
~~~~~~~~~~~~~~

This module provides glob access.
"""

from bitgen.patterns import Subject
from bitgen.glob import Collector


# define a singleton for strategy behavior pattern
class OmniModel(Collector):
    """controller singleton for strategy purpose"""
    def __init__(self):
        super().__init__()
        self.mount('PERS_DATA')
        self.pers_data = self.collection['PERS_DATA'].config


# define a default model
class DefaultModel(Subject):
    def __init__(self, supervisor):
        super().__init__()
        self.attach(supervisor)