#!/usr/bin/env python

"""
forecaster.security.preserver
~~~~~~~~~~~~~~

Facade class to preserve profits.
"""
import logging

from forecaster.utils import read_strategy

logger = logging.getLogger('forecaster.predict')


# TODO: add utility to this module
class Preserver(object):
    """main preserver"""

    def __init__(self, strat):
        self.strategy = read_strategy(strat)['preserver']
        logger.debug("Preserver initied")
