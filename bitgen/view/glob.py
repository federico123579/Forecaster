# -*- coding: utf-8 -*-

"""
bitgen.view.glob
~~~~~~~~~~~~~~

This module provides glob access.
"""

from bitgen.patterns import Subject
from bitgen.glob import Collector


# define a singleton for strategy behavior pattern
class OmniViewer(Collector):
    """viewer singleton for strategy purpose"""
    def __init__(self):
        super().__init__()
        self.mount('SECURITY_DATA')
        self.security = self.collection['SECURITY_DATA'].config


# define a default viewer
class DefaultViewer(Subject):
    def __init__(self, supervisor):
        super().__init__()
        self.attach(supervisor)
