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
        self.currencies = [x[0] for x in self.strategy['currencies']]
        self.timeframe = self.strategy['timeframe']
        #self.timeframe = [time_trans, TIMEFRAME[time_trans]]
        self.transactions = []
        # AUTONOMOUS MODULES
        self.preserver = Preserver(self.strategy)
        self.positioner = Positioner(self.strategy)
        self.LOOP = Event()
        # ADDED IN ALPHA2
        self.seconds_to_wait = self.strategy['seconds_to_wait']
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
        # EDITED IN ALPHA2
        self.LOOP.set()
        ThreadHandler().add_event(self.LOOP)
        thread = LogThread(target=self.check_closes)  # check closes
        thread.start()
        ThreadHandler().add_thread(thread)
        LOGGER.debug("check_closes thread started")
        # TODO: check the behavior of this
        # self.positioner.start()
        LOGGER.debug("AUTOMATON: started")

    def stop(self):
        """stop threads"""
        self.positioner.stop()
        self.LOOP.clear()
        LOGGER.debug("AUTOMATON: stopped")

    def check_closes(self):
        """first thread loop - check close"""
        # EDITED IN ALPHA2
        while self.LOOP.is_set():
            start = time.time()
            while not any(Client().check_if_market_open(self.currencies)):
                LOGGER.debug(f"Market closed for all symbol requested, waiting "
                             f"{self.seconds_to_wait} seconds")
                wait(self.seconds_to_wait, self.LOOP)
            symbol_open = [sym for sym, val in Client().check_if_market_open(
                    self.currencies).items() if val]
            LOGGER.debug(f"working with {', '.join(symbol_open)}")
            self._open_transactions(symbol_open)
            self._complete_transactions()
            wait_precisely(self.strategy['sleep_transactions'], start, self.LOOP)

    def _open_transactions(self, symbol_open_market_list):
        """(1/2) init all transactions"""
        # EDITED IN ALPHA2
        for symbol in symbol_open_market_list:
             # if self.preserver.check_high_risk(symbol):
             #     if not self.preserver.allow_high_risk:
             #         continue

            args = [symbol, self.strategy['timeframe'], self.strategy['count']]
            action = self.handle_request(ACTIONS.PREDICT, args=args)
            if action in [ACTIONS.BUY, ACTIONS.SELL]:
                self.transactions.append(Transaction(symbol, action, self))
            else:
                pass
        for trans in self.transactions:
            trans.compose()
            #LOGGER.debug("{} score: {}".format(trans.symbol, trans.score))
        LOGGER.debug("opened {} transactions".format(len(self.transactions)))

    def _complete_transactions(self):
        """(2/2) complete all transactions"""
        old_len_pos = Client().get_position_len()
        with ThreadPoolExecutor(10) as executor:
            trans_list = self.transactions
            trans_list = trans_list[:self.preserver.concurrent_movements -
                                    old_len_pos]
            for trans in trans_list:
                executor.submit(trans.complete)
        LOGGER.debug("completed {} transactions".format(
            Client().get_position_len() - old_len_pos))
        self.handle_request(EVENTS.OPENED_POS,
                            number=Client().get_position_len() - old_len_pos)
        self.transactions.clear()

#    def _market_open(self):
#        """get time left to update of hist data"""
#        # EDITED IN ALPHA2
#        market_op_symbols = Client().check_if_market_open(self.currencies)
#        for symbol in market_op_symbols.keys():
#            if market_op_symbols[symbol]:
#
#        # hist = Client().api.get_historical_data('EURUSD', 1,
#        # self.timeframe[0])
#        # last_time = int(hist[0]['timestamp']) / 1000  # remove milliseconds
#        # time_left = self.timeframe[1] - (time.time() - last_time) #+ 3600
#        # # ADDED FOR LEGAL HOUR#
#        # while time_left < 0:  # skip cycles#
#        #     time_left += self.timeframe[1]#
#        # LOGGER.debug("time left (in minutes): {}".format(time_left / 60))#
#        return time_left


class Transaction(object):
# EDITED IN ALPHA2
    def __init__(self, symbol, automaton, mode):
        self.auto = automaton
        self.symbol = symbol
        self.fix = automaton.strategy['fix_trend']
        self.fix_quant = automaton.strategy['fixed_quantity']
        self.mode = mode
        #self.score = 0

    def compose(self):
        """complete mode and quantity"""
        #self.mode = self._get_mode()
        self.quantity = self._get_quantity()
        #args = [self.symbol, self.auto.strategy['count'],
        # self.auto.strategy['timeframe']]
        #self.score = self.auto.handle_request(ACTIONS.SCORE, args=args)

    def complete(self):
        try:
            Client().refresh()
            poss = [pos for pos in Client().positions if pos.symbol ==
                    self.symbol]
            if self.fix:  # if requested to fix
                self._fix_trend(poss, self.mode)
            self.open()
            LOGGER.debug("transaction with score of {:.4f} completed".format(self.score))
        except Exception as e:
            LOGGER.error(e)

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

    #def _get_mode(self):
    #    args = [self.symbol, self.auto.strategy['timeframe'],
    #            self.auto.strategy['count']]
    #    return self.auto.handle_request(ACTIONS.PREDICT, args=args)

    def _get_quantity(self):
        quantity = [x[1] for x in self.auto.strategy['currencies'] if x[0] == self.symbol][0]
        if self.fix_quant:
            return quantity
        else:
            raise NotImplementedError()
            # TODO with handle_request(ACTIONS.GET_USABLE_MARGIN)
