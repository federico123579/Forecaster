# -*- coding: utf-8 -*-

"""
forecaster.core.view.glob
~~~~~~~~~~~~~~

This module provides glob access.
"""

from forecaster.patterns import Subject
from forecaster.glob import Collector


# define a singleton for strategy behavior pattern
class OmniViewer(Collector):
    """viewer singleton for strategy purpose"""
    def __init__(self):
        super().__init__()
        self.mount('SECURITY_DATA')
        self.mount('PERS_DATA')
        self.security = self.collection['SECURITY_DATA'].config
        self.pers_data = self.collection['PERS_DATA'].config


# define a default viewer
class DefaultViewer(Subject):
    def __init__(self, supervisor):
        super().__init__()
        self.attach(supervisor)
