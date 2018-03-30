#!/usr/bin/env python

"""
forecaster.security.preserver
~~~~~~~~~~~~~~

Facade class to preserve profits.
"""

import logging

from forecaster.handler import Client

LOGGER = logging.getLogger('forecaster.predict')


class Preserver(object):
    """module that preserve funds"""

    def __init__(self, strat):
        self.strategy = strat['preserver']
        self.funds_risk = self.strategy['funds_risk']
        LOGGER.debug("Preserver initied")

    def check_margin(self, symbol, quantity):
        """check if margin allows more buys"""
        free = self.get_free_margin()
        to_use = Client().get_margin(symbol, quantity)
        if to_use <= free:
            return True
        else:
            return False

    def get_free_margin(self):
        """get free margin left"""
        Client().refresh()
        total_funds = Client().funds['total']
        free_funds = Client().funds['free']
        used_funds = total_funds - free_funds
        avaible_margin = self.funds_risk * total_funds - used_funds
        return max(avaible_margin, 0)
