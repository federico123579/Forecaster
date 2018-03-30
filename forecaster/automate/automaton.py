"""
forecaster.automate.automaton
~~~~~~~~~~~~~~

Proxy class to automate algorithms.
"""

import logging
import time
from threading import Event

from forecaster.automate.positioner import Positioner
from forecaster.automate.utils import LogThread, ThreadHandler, wait, wait_precisely
from forecaster.enums import ACTIONS, TIMEFRAME
from forecaster.handler import Client
from forecaster.patterns import Chainer
from forecaster.security import Preserver
from forecaster.utils import read_strategy

LOGGER = logging.getLogger('forecaster.automate')


class Automaton(Chainer):
    """Adapter and Mediator for autonomous capability"""

    def __init__(self, strat, bot):
        super().__init__(bot)
        self.strategy = read_strategy(strat)
        time_trans = self.strategy['timeframe']
        self.timeframe = [time_trans, TIMEFRAME[time_trans]]
        # AUTONOMOUS MODULES
        self.preserver = Preserver(self.strategy)
        self.positioner = Positioner(self.strategy)
        self.LOOP = Event()
        LOGGER.debug("AUTOMATON: ready")

    def handle_request(self, event, **kw):
        """handle requests from chainers"""
        return self.pass_request(event, **kw)

    def start(self):
        """start threads"""
        self.LOOP.set()
        ThreadHandler().add_event(self.LOOP)
        thread = LogThread(target=self.check_closes)  # check closes
        thread.start()
        ThreadHandler().add_thread(thread)
        LOGGER.debug("check_closes thread started")
        self.positioner.start()
        LOGGER.debug("AUTOMATON: started")

    def stop(self):
        """stop threads"""
        self.positioner.stop()
        self.LOOP.clear()
        LOGGER.debug("AUTOMATON: stopped")

    def check_closes(self):
        """loop check closes"""
        wait(self._time_left(), self.LOOP)
        while self.LOOP.is_set():
            start = time.time()
            for symbol in self.strategy['currencies']:
                tran = Transaction(symbol, self)
                tran.complete()
            wait_precisely(self.strategy['sleep_transactions'], start, self.LOOP)

    def _time_left(self):
        """get time left to update of hist data"""
        # check EURUSD for convention
        hist = Client().api.get_historical_data('EURUSD', 1, self.timeframe[0])
        last_time = int(hist[0]['timestamp']) / 1000  # remove milliseconds
        time_left = self.timeframe[1] - (time.time() - last_time)
        LOGGER.debug("time left (in minutes): {}".format(time_left / 60))
        return time_left


class Transaction(object):
    def __init__(self, symbol, automaton):
        self.auto = automaton
        self.symbol = symbol
        self.mode = self._get_mode()
        self.quantity = automaton.strategy['fixed_quantity']
        self.fix = automaton.strategy['fix_trend']

    def complete(self):
        Client().refresh()
        poss = [pos for pos in Client().api.positions if pos.instrument == self.symbol]
        if self.mode == ACTIONS.BUY:
            if self.fix:  # if requested to fix
                self._fix_trend(poss, 'sell')
            self.open()
        elif self.mode == ACTIONS.SELL:
            if self.fix:  # if requested to fix
                self._fix_trend(poss, 'buy')
            self.open()
        LOGGER.debug("transaction completed")

    def open(self):
        if not self.auto.preserver.check_margin(self.symbol, self.quantity):
            LOGGER.warning("Transaction can't be executed due to missing funds")
        if self.mode == ACTIONS.BUY:
            Client().open_pos(self.symbol, 'buy', self.quantity)
        if self.mode == ACTIONS.SELL:
            Client().open_pos(self.symbol, 'sell', self.quantity)

    def _get_mode(self):
        args = [self.symbol, self.auto.strategy['count'], self.auto.strategy['timeframe']]
        return self.auto.handle_request(ACTIONS.PREDICT, args=args)

    def _fix_trend(self, poss, mode):
        pos_left = [x for x in poss if x.mode == mode]  # get position of mode
        LOGGER.debug("{} trends to fix".format(len(pos_left)))
        if pos_left:  # if existent
            for pos in pos_left:  # iterate over
                LOGGER.debug("fixing trend for {}".format(pos.instrument))
                Client().close_pos(pos)
