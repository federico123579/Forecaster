"""
forecaster.handler
~~~~~~~~~~~~~~

Handle requests and responses from API
"""

import logging
import time

import raven
import trading212api
from forecaster import __version__
from forecaster.enums import EVENTS
from forecaster.exceptions import MissingData
from forecaster.patterns import Chainer, Singleton, State, StateContext
from forecaster.utils import read_data, read_strategy, read_tokens

logger = logging.getLogger('forecaster.handler')
mover_logger = logging.getLogger('mover')


class Client(Chainer, StateContext, metaclass=Singleton):
    """UI module with APIs"""

    def __init__(self, strat='default', bot=None):
        self.strategy = read_strategy(strat)['handler']
        curr_state = get_state_mode(self.strategy['mode'])
        super().__init__(successor=bot, state=curr_state)
        self.api = None
        self.handle_state('init')  # set api
        self.RESULTS = 0.0  # current net profit
        logger.debug("CLIENT: initied")

    def handle_request(self, event, **kw):
        """pattern function"""
        if event == EVENTS.CHANGE_MODE:
            mode = kw['mode']
            if self._state.mode != mode:
                logger.info("CLIENT: switching mode from {} to {}".format(
                    self._state.mode, mode))
                self.swap()
                self._auto_login()
                logger.info(
                    "CLIENT: current mode: {}".format(self._state.mode))
        else:
            self.pass_request(event, **kw)

    def start(self):
        """start from credentials in data file"""
        self.data = self._get_data()
        self._auto_login()
        logger.debug("CLIENT: started with data")

    def _get_data(self):
        """get credentials if exist"""
        try:
            return read_data('data')
        except FileNotFoundError:
            raise MissingData()

    def _auto_login(self):
        """"auto login with credentials"""
        self.login(self.data['username'], self.data['password'])

    def login(self, username, password):
        """log in trading212"""
        while True:
            try:
                self.api.login(username, password)
                break
            except trading212api.exceptions.InvalidCredentials as e:
                logger.error("Invalid credentials with {}".format(e.username))
                self.handle_request(EVENTS.MISSING_DATA)
            except trading212api.exceptions.LiveNotConfigured:
                logger.error("{} mode not configured".format(self.mode))
                self.handle_request(EVENTS.MODE_FAILURE)
        logger.debug("CLIENT: logged in")

    def open_pos(self, symbol, mode, quantity):
        """open position and handle exceptions"""
        self.refresh()  # renovate sessions
        while True:  # handle exceptions
            try:
                self.api.open_position(mode, symbol, quantity)
                mover_logger.info(
                    "opened position of {:d} {} on {}".format(quantity, symbol, mode))
                break
            except trading212api.exceptions.PriceChangedException:
                continue
            except trading212api.exceptions.MaxQuantityExceeded:
                logger.warning("Maximum quantity exceeded")
                break
            except trading212api.exceptions.MarketClosed:
                logger.warning("Market closed for {}".format(symbol))
                self.handle_request(EVENTS.MARKET_CLOSED, sym=symbol)
                break
            except trading212api.exceptions.ProductNotAvaible:
                logger.warning("Product not avaible")
                SentryClient().captureException()
                break

    def close_pos(self, pos):
        """close position and update results"""
        self.refresh()  # renovate sessions
        while True:
            try:
                self.api.close_position(pos.id)  # close
                mover_logger.info("closed position {}".format(pos.id))
                mover_logger.info("gain: {:.2f}".format(pos.result))
                break
            except trading212api.exceptions.NoPriceException:
                logger.warning("NoPriceException caught")
                time.sleep(1)  # waiting 1 second
            except ValueError:
                logger.warning("Position not found")
                break
        self.RESULTS += pos.result  # update returns
        self.handle_request(EVENTS.CLOSED_POS, pos=pos)

    def close_all(self):
        self.refresh()
        poss = []
        for pos in self.api.account.positions:
            poss.append(pos)
        for pos in poss:  # avoid continue refresh
            self.close_pos(pos)

    def get_last_candles(self, symbol, num, timeframe):
        self.refresh()  # renovate sessions
        candles = self.api.get_historical_data(symbol, num, timeframe)
        prices = [candle['bid'] for candle in candles]
        return prices

    def refresh(self):
        try:
            self.api.refresh()
        except trading212api.exceptions.RequestError:
            logger.warning("API unavaible")
            self._auto_login()
            self.api.refresh()

    def swap(self):
        """swap mode"""
        self.handle_state('swap')
        self.handle_state('init')
        self.RESULTS = 0.0


def get_state_mode(mode):
    """get state from mode"""
    if mode not in ['demo', 'live']:
        raise ValueError("mode not acceptable")
    if mode == 'demo':
        return DemoModeState()
    elif mode == 'live':
        return LiveModeState()


class ModeState(State):
    """mode abstract state"""

    def __init__(self, mode):
        self.mode = mode
        self.actions = ['init', 'swap']

    def handle(self, context, action):
        if action not in self.actions:
            raise ValueError("actions not permitted")
        if action == 'init':
            context.api = trading212api.Client(self.mode)
            context.mode = self.mode
        if action == 'swap':
            self.swap(context)

    def swap(self, context):
        raise NotImplementedError()


class DemoModeState(ModeState):
    def __init__(self):
        super().__init__('demo')

    def swap(self, context):
        context.set_state(LiveModeState())


class LiveModeState(ModeState):
    def __init__(self):
        super().__init__('live')

    def swap(self, context):
        context.set_state(DemoModeState())


class SentryClient(raven.Client, metaclass=Singleton):
    """sentry handler to handle exceptions"""

    def __init__(self, *args, **kwargs):
        token = read_tokens()['sentry']
        version = __version__.strip('v')
        env = 'developing'
        super().__init__(dsn=token, release=version, environment=env, *args, **kwargs)
        logger.debug("SENTRY: initied")
