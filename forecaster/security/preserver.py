#!/usr/bin/env python

"""
forecaster.security.preserver
~~~~~~~~~~~~~~

Facade class to preserve profits.
"""
import logging

from forecaster.utils import read_strategy

logger = logging.getLogger('forecaster.predict')


class Preserver(object):
    """main preserver"""

    def __init__(self, strat):
        self.strategy = read_strategy(strat)['preserver']
        logger.debug("Preserver initied")

    def check_position_relative(self, position):
        """check stop limits"""
        perc = position.price / position.current_price
        if perc >= self.strategy['relative']['gain']:
            logger.debug("position gain %.2f%%" % (100 * perc))
            return 'CLOSE_POS'
        if perc <= self.strategy['relative']['loss']:
            logger.debug("position loss %.2f%%" % (100 * perc))
            return 'CLOSE_POS'

    def check_position_fixed(self, position):
        """check stop limits"""
        profit = position.result
        if profit >= self.strategy['fixed']['gain']:
            logger.debug("position gain %.2f" % profit)
            return 'CLOSE_POS'
        if profit <= self.strategy['fixed']['loss']:
            logger.debug("position loss %.2f" % profit)
            return 'CLOSE_POS'
