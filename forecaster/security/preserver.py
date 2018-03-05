#!/usr/bin/env python

"""
forecaster.security.preserver
~~~~~~~~~~~~~~

Facade class to preserve profits.
"""
import logging

from forecaster.handler import Client
from forecaster.utils import read_strategy

logger = logging.getLogger('forecaster.predict')


class Preserver(object):
    """main preserver"""

    def __init__(self, strat):
        self.strategy = read_strategy(strat)['preserver']
        self.funds_risk = self.strategy['funds_risk']
        logger.debug("Preserver initied")

    def check_margin(self, symbol, quantity):
        free = self.get_free_margin()
        to_use = Client().api.get_margin(symbol, quantity)
        if to_use <= free:
            return True
        else:
            return False

    def get_free_margin(self):
        Client().refresh()
        total_funds = Client().api.account.funds['total']
        free_funds = Client().api.account.funds['free']
        used_funds = total_funds - free_funds
        avaible_margin = self.funds_risk * total_funds - used_funds
        return max(avaible_margin, 0)
