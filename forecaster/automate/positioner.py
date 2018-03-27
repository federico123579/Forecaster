"""
forecaster.automate.positioner
~~~~~~~~~~~~~~

Class to handle positions.
"""

import logging

from forecaster.automate.checkers import FactoryChecker
from forecaster.automate.filters import FilterWrapper
from forecaster.automate.utils import ACTIONS
from forecaster.patterns import Chainer
from forecaster.utils import read_strategy

logger = logging.getLogger('forecaster.automate.positioner')


class Positioner(Chainer):
    """handle all positions"""

    def __init__(self, strat, auto_strat, predicter):
        self.predicter = predicter
        strat = read_strategy(strat)
        self.strategy = strat['positioner']
        self.auto_strategy = auto_strat  # keep for checkers
        # FILTER
        self.filter = FilterWrapper(strat['filter'], self)
        # CHECKERS
        self.checkers_strat = strat['checkers']
        self.pos_checks = {x[0]: x[1]['activate'] for x in strat['checkers'].items()}
        self.checkers = []
        logger.debug("POSITIONER: ready")

    def handle_request(self, event, **kw):
        """handle request"""
        if event == ACTIONS.CLOSE:
            self.filter.check(kw['pos'])  # pass to filters
        else:
            self.pass_request(event, **kw)

    def start(self):
        """stop positioner"""
        self._check_checker('relative')
        self._check_checker('reversion')
        self._check_checker('fixed')
        logger.debug("POSITIONER: started")

    def stop(self):
        """stop positioner"""
        for checker in self.checkers:
            checker.stop()
        logger.debug("POSITIONER: stopped")

    def _check_checker(self, name):
        if self.pos_checks[name]:
            checker = FactoryChecker[name](self.checkers_strat[name], self)
            self.checkers.append(checker)
            checker.start()
