"""
forecaster.automate.automaton
~~~~~~~~~~~~~~

Proxy class to automate algorithms.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event

from forecaster.automate.positioner import Positioner
from forecaster.automate.utils import LogThread, ThreadHandler, wait, wait_precisely
from forecaster.enums import ACTIONS, EVENTS, TIMEFRAME
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
        self.transactions = []
        # AUTONOMOUS MODULES
        self.preserver = Preserver(self.strategy)
        self.positioner = Positioner(self.strategy)
        self.LOOP = Event()
        LOGGER.debug("AUTOMATON: ready")

    def handle_request(self, request, **kw):
        """handle requests from chainers"""
        # get usable margin for calculating quantities
        if request == ACTIONS.GET_USABLE_MARGIN:
            return self.preserver.get_usable_margin()
        else:
            return self.pass_request(request, **kw)

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
        """first thread loop - check close"""
        wait(self._time_left() + 5, self.LOOP)  # refresh servers
        while self.LOOP.is_set():
            start = time.time()
            self._open_transactions()
            self._compose_transactions()
            self._complete_transactions()
            wait_precisely(self.strategy['sleep_transactions'], start, self.LOOP)

    def _open_transactions(self):
        """(1/3) init all transactions"""
        for symbol in [x[0] for x in self.strategy['currencies']]:
            if self.preserver.check_high_risk(symbol):
                if not self.preserver.allow_high_risk:
                    continue
            self.transactions.append(Transaction(symbol, self))
        LOGGER.debug("opened {} transactions".format(len(self.transactions)))

    def _compose_transactions(self):
        """(2/3) compose all transactions"""
        with ThreadPoolExecutor(10) as executor:
            for trans in self.transactions:
                executor.submit(trans.compose)
        LOGGER.debug("composed {} transactions".format(len(self.transactions)))

    def _complete_transactions(self):
        """(3/3) complete all transactions"""
        old_len_pos = len(Client().positions)
        with ThreadPoolExecutor(10) as executor:
            scores = sorted(self.transactions, key=lambda x: x.score)
            scores = scores[::-1][:self.preserver.concurrent_movements]
            for trans in scores:
                executor.submit(trans.complete)
        LOGGER.debug("completed {} transactions".format(len(Client().positions) - old_len_pos))
        self.handle_request(EVENTS.OPENED_POS, number=len(Client().positions) - old_len_pos)
        self.transactions.clear()

    def _time_left(self):
        """get time left to update of hist data"""
        # check EURUSD for convention
        hist = Client().api.get_historical_data('EURUSD', 1, self.timeframe[0])
        last_time = int(hist[0]['timestamp']) / 1000  # remove milliseconds
        time_left = self.timeframe[1] - (time.time() - last_time)
        while time_left < 0:  # skip cycles
            time_left += self.timeframe[1]
        LOGGER.debug("time left (in minutes): {}".format(time_left / 60))
        return time_left


class Transaction(object):
    def __init__(self, symbol, automaton):
        self.auto = automaton
        self.symbol = symbol
        self.fix = automaton.strategy['fix_trend']
        self.fix_quant = automaton.strategy['fixed_quantity']

    def compose(self):
        """complete mode and quantity"""
        self.mode = self._get_mode()
        self.quantity = self._get_quantity()
        args = [self.symbol, self.auto.strategy['count'], self.auto.strategy['timeframe']]
        self.score = self.auto.handle_request(ACTIONS.SCORE, args=args)

    def complete(self):
        Client().refresh()
        poss = [pos for pos in Client().positions if pos.instrument == self.symbol]
        if self.fix:  # if requested to fix
            self._fix_trend(poss, self.mode)
        self.open()
        LOGGER.debug("transaction with score of {:.4f} completed".format(self.score))

    def open(self):
        if not self.auto.preserver.check_margin(self.symbol, self.quantity):
            LOGGER.warning("Transaction can't be executed due to missing funds")
        if self.mode == ACTIONS.BUY:
            Client().open_pos(self.symbol, 'buy', self.quantity)
        if self.mode == ACTIONS.SELL:
            Client().open_pos(self.symbol, 'sell', self.quantity)

    def _fix_trend(self, poss, mode):
        if mode == ACTIONS.BUY:
            raw_mode = 'sell'
        elif mode == ACTIONS.SELL:
            raw_mode = 'buy'
        pos_left = [x for x in poss if x.mode == raw_mode]  # get position of mode
        LOGGER.debug("{} trends to fix".format(len(pos_left)))
        if pos_left:  # if existent
            for pos in pos_left:  # iterate over
                LOGGER.debug("fixing trend for {}".format(pos.instrument))
                Client().close_pos(pos)

    def _get_mode(self):
        args = [self.symbol, self.auto.strategy['count'], self.auto.strategy['timeframe']]
        return self.auto.handle_request(ACTIONS.PREDICT, args=args)

    def _get_quantity(self):
        quantity = [x[1] for x in self.auto.strategy['currencies'] if x[0] == self.symbol][0]
        if self.fix_quant:
            return quantity
        else:
            raise NotImplementedError()
            # TODO with handle_request(ACTIONS.GET_USABLE_MARGIN)
