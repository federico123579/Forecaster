"""
forecaster.automate.automaton
~~~~~~~~~~~~~~

Proxy class to automate algorithms.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum, auto
from threading import Event

from forecaster.automate.positioner import Positioner
from forecaster.automate.utils import LogThread, ThreadHandler, wait, wait_precisely
from forecaster.enums import ACTIONS, EVENTS, TIMEFRAME
from forecaster.exceptions import TransactionDiscarded
from forecaster.handler import Client
from forecaster.patterns import Chainer
from forecaster.security import Preserver

LOGGER = logging.getLogger('forecaster.automate')


class Automaton(Chainer):
    """Adapter and Mediator for autonomous capability"""

    def __init__(self, bot, strategy):
        super().__init__()
        self.attach_successor(bot)
        self.strategy = strategy
        time_trans = self.strategy['timeframe']
        self.timeframe = [time_trans, TIMEFRAME[time_trans]]
        self.transactions = []
        # INIT SINGLETON MODULES
        self.client = Client()
        self.preserver = Preserver()
        # AUTONOMOUS MODULES
        self.positioner = Positioner(self.strategy, self)
        self.LOOP = Event()
        LOGGER.debug("AUTOMATON: ready")

    def handle_request(self, request, **kw):
        """handle requests from chainers"""
        # get score or mode by prediction
        if request == ACTIONS.PREDICT:
            args = [self.strategy['count'], self.strategy['timeframe']]
            args.insert(0, kw['symbol'])
            return self.pass_request(request, args=args)
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
                try:
                    trans.compose()
                except Exception as e:
                    LOGGER.exception(e)
                executor.submit(trans.compose)
        LOGGER.debug("composed {} transactions".format(len(self.transactions)))

    def _complete_transactions(self):
        """(3/3) complete all transactions"""
        old_len_pos = len(self.client.positions)
        with ThreadPoolExecutor(10) as executor:
            scores = sorted(self.transactions, key=lambda x: x.score)
            scores = scores[::-1][:self.preserver.concurrent_movements]
            for trans in scores:
                executor.submit(trans.complete)
        completed_trans = len(self.client.positions) - old_len_pos
        LOGGER.debug("completed {} transactions".format(completed_trans))
        self.handle_request(EVENTS.OPENED_POS, number=completed_trans)
        self.transactions.clear()

    def _time_left(self):
        """get time left to update of hist data"""
        # check EURUSD for convention
        hist = self.client.api.get_historical_data('EURUSD', 1, self.timeframe[0])
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
        self.status = TransactionStates.INITIED

    def compose(self):
        """complete mode and quantity"""
        prediction = self.auto.handle_request(ACTIONS.PREDICT, symbol=self.symbol)
        try:  # catch discarded transaction
            self.mode = self._get_mode(prediction)
        except TransactionDiscarded:
            self.score = 0
            self.status = TransactionStates.DISCARDED
            return  # stop
        self.quantity = self._get_quantity(prediction)
        self.score = prediction.score
        self.status = TransactionStates.COMPOSED

    def complete(self):
        """complete and open transaction"""
        if self.status != TransactionStates.COMPOSED:
            return  # abort in case of stopped
        Client().refresh()
        poss = [pos for pos in Client().positions if pos.instrument == self.symbol]
        self._fix_trend(poss, self.mode)
        self.open()
        LOGGER.debug("transaction with score of {:.4f} completed".format(self.score))
        self.status = TransactionStates.COMPLETED

    def open(self):
        """check margin and send request to client"""
        if not self.auto.preserver.check_margin(self.symbol, self.quantity):
            LOGGER.warning("Transaction can't be executed due to missing funds")
        Client().open_pos(self.symbol, self.mode, self.quantity)

    def _fix_trend(self, poss, mode):
        """close all positions of opposite way"""
        if not self.fix:
            return  # if requested to fix
        pos_left = [x for x in poss if x.mode == self.mode]  # get position of mode
        LOGGER.debug("{} trends to fix".format(len(pos_left)))
        if pos_left:  # if existent
            for pos in pos_left:  # iterate over
                LOGGER.debug("fixing trend for {}".format(pos.instrument))
                Client().close_pos(pos)

    def _get_mode(self, prediction):
        """get mode from prediction"""
        if prediction.action == ACTIONS.BUY:
            return 'buy'
        elif prediction.action == ACTIONS.SELL:
            return 'sell'
        elif prediction.action == ACTIONS.DISCARD:
            LOGGER.debug("{} discarded".format(self.symbol))
            raise TransactionDiscarded(prediction)  # abort transaction

    def _get_quantity(self, prediction):
        """get quantity based on prediction and score"""
        min_quantity = [x[1] for x in self.auto.strategy['currencies'] if x[0] == self.symbol][0]
        margin = self.auto.strategy['margin_to_use']
        margin_per_unit = Client().get_margin(self.symbol, min_quantity) / min_quantity
        return int(margin / Preserver().concurrent_movements / margin_per_unit)


class TransactionStates(Enum):
    INITIED = auto()
    COMPOSED = auto()
    COMPLETED = auto()
    DISCARDED = auto()
