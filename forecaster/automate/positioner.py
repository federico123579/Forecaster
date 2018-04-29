"""
forecaster.automate.positioner
~~~~~~~~~~~~~~

Autonomous module that handle all positions.
"""

import logging

from forecaster.automate.checkers import FactoryChecker
from forecaster.automate.utils import ACTIONS
from forecaster.handler import Client
from forecaster.patterns import Chainer

LOGGER = logging.getLogger('forecaster.automate.positioner')


class Positioner(Chainer):
    """module that handle positions"""

    def __init__(self, strat, bot=None):
        super().__init__(bot)
        self.auto_strategy = strat  # keep for checkers
        self.checkers_strat = strat['checkers']
        self.pos_checks = self.checkers_strat['activate']
        self.checkers = []
        LOGGER.debug("POSITIONER: ready")

    def handle_request(self, event, **kw):
        """handle requests from chainers"""
        if event == ACTIONS.CLOSE:
            LOGGER.debug("{} checker triggered for {}".format(kw['checker'], kw['pos'].id))
            Client().close_pos(kw['pos'])
        if event == ACTIONS.CLOSE_ALL:
            LOGGER.debug("{} checker triggered for closing {} positions".format(
                kw['checker'], len(Client().positions)))
            Client().close_all()
        elif event == ACTIONS.KEEP:
            LOGGER.debug("{} checker keeps position {}".format(kw['checker'], kw['pos'].id))
        else:
            self.pass_request(event, **kw)

    def start(self):
        """start positioner"""
        for name in self.pos_checks:
            checker = FactoryChecker[name](self.checkers_strat[name], self)
            self.checkers.append(checker)
            checker.start()
        LOGGER.debug("POSITIONER: started")

    def stop(self):
        """stop positioner"""
        for checker in self.checkers:
            checker.stop()
        LOGGER.debug("POSITIONER: stopped")
