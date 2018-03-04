#!/usr/bin/env python

"""
forecaster.automate.positioner
~~~~~~~~~~~~~~

Class to handle positions.
"""
import logging

from forecaster.automate.checkers import *
from forecaster.automate.filters import FilterWrapper
from forecaster.automate.utils import ACTIONS
from forecaster.utils import Chainer, read_strategy

logger = logging.getLogger('forecaster.automate.positioner')


class Positioner(Chainer):
    """handle all positions"""

    def __init__(self, strat, auto_strat, preserver, predicter):
        self.preserver = preserver
        self.predicter = predicter
        strat = read_strategy(strat)
        self.strategy = strat['positioner']
        self.auto_strategy = auto_strat  # keep for checkers
        # FILTER
        self.Filter = FilterWrapper(strat['filter'])
        # CHECKERS
        self.checkers_strat = strat['checkers']
        self.pos_checks = {x[0]: x[1]['activate'] for x in strat['checkers'].items()}
        self.checkers = []
        logger.debug("Positioner initied")

    def handle_request(self, event, **kw):
        if event == ACTIONS.CLOSE:
            self.Filter.check(kw['pos'])  # pass to filters

    def start(self):
        self._check_checker('relative')
        self._check_checker('reversion')
        self._check_checker('fixed')

    def stop(self):
        for checker in self.checkers:
            checker.stop()

    def _check_checker(self, name):
        if self.pos_checks[name]:
            checker = FactoryChecker[name](self.checkers_strat[name], self)
            self.checkers.append(checker)
            checker.start()
