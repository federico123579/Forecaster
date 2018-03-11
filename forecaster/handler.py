"""
forecaster.handler
~~~~~~~~~~~~~~

Handle requests and responses from API
"""
import logging

import raven
import trading212api
from forecaster import __VERSION__
from forecaster.exceptions import MissingData
from forecaster.patterns import Chainer, Singleton, State, StateContext
from forecaster.utils import read_strategy
from trading212api.exceptions import *

logger = logging.getLogger('forecaster.handler')
mover_logger = logging.getLogger('mover')


class Client(metaclass=Singleton):
    """UI module with APIs"""

    def __init__(self, strat='default', bot=None):
        Chainer.__init__(self, bot)
        self.strategy = read_strategy(strat)['handler']
        curr_state = get_state_mode(self.strategy['mode'])
        StateContext.__init__(self, curr_state)
        self.handle_state('init')  # set api
        self.RESULTS = 0.0  # current net profit
        logger.debug("CLIENT: initied")

    def handle_request(self, event, **kw):
        """pattern function"""
        self.pass_request(event, **kw)

    def start(self):
        """start from credentials in data file"""
        self.data = self._get_data()
        self._auto_login()
        logger.debug("CLIENT: started with data")

    def _get_data(self):
        """get credentials if exist"""
        try:
            return read_strategy('data')
        except FileNotFoundError:
            raise MissingData()

    def _auto_login(self):
        """"auto login with credentials"""
        self.login(self.data['username'], self.data['password'])

    def login(self, username, password):
        """log in trading212"""
        try:
            self.api.login(username, password)
        except InvalidCredentials as e:
            logger.error("Invalid credentials with %s" % e.username)
            self.handle_request(EVENTS.MISSING_DATA)
        logger.debug("CLIENT: logged in")

    def open_pos(self, symbol, mode, quantity):
        """open position and handle exceptions"""
        self.refresh()  # renovate sessions
        while True:  # handle exceptions
            try:
                self.api.open_position(mode, symbol, quantity)
                mover_logger.info("opened position of %d %s on %s" (quantity, symbol, mode))
                break
            except PriceChangedException as e:
                continue
            except MaxQuantityExceeded as e:
                logger.warning("Maximum quantity exceeded")
                break
            except ProductNotAvaible as e:
                logger.warning("Product not avaible")
                SentryClient().captureException()
                break

    def close_pos(self, pos):
        """close position and update results"""
        self.refresh()  # renovate sessions
        while True:
            try:
                self.api.close_position(pos.id)  # close
                mover_logger.info("closed position %s" pos.id)
                mover_logger.info("gain: %.2f" pos.result)
                break
            except NoPriceException as e:
                logger.warning("NoPriceException caught")
                SentryClient().captureException()
            except ValueError as e:
                logger.warning("Position not found")
                break
        self.RESULTS += pos.result  # update returns
        self.handle_request(EVENTS.CLOSED_POS, pos=pos)

    def close_all(self):
        self.refresh()
        ids = []
        for pos in self.api.account.positions:
            ids.append(pos.id)
        for id in ids:  # avoid continue refresh
            self.close_pos(id)

    def get_last_candles(self, symbol, num, timeframe):
        self.refresh()  # renovate sessions
        candles = self.api.get_historical_data(symbol, num, timeframe)
        prices = [candle['bid'] for candle in candles]
        return prices

    def refresh(self):
        try:
            self.api.refresh()
        except RequestError as e:
            logger.warning("API unavaible")
            self.login()
            self.api.refresh()

    def swap(self):
        """swap mode"""
        self.handle_state('swap')


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
        if action not self.actions:
            raise ValueError("actions not permitted")
        if action == 'init':
            context.api = trading212api.Client(self.mode)
        if action == 'swap':
            self.swap(context)

    def swap(self):
        raise NotImplementedError()


class DemoModeState(ModeState):
    def __init__(self):
        super().__init__('demo')

    def swap(self, context):
        self.context.set_state(LiveModeState())


class LiveModeState(ModeState):
    def __init__(self):
        super().__init__('live')

    def swap(self, context):
        self.context.set_state(DemoModeState())


class SentryClient(metaclass=Singleton):
    """sentry handler to handle exceptions"""

    def __init__(self, *args, **kwargs):
        token = os.environ['FORECASTER_SENTRY_TOKEN']
        version = __VERSION__.strip('v')
        sample_rate = 1
        raven.Client.__init__(self, token, version, *args, **kwargs)
        logger.debug("SENTRY: initied")
