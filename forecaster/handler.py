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
from forecaster.patterns import Chainer, Singleton
from forecaster.utils import get_conf, read_data, read_tokens

logger = logging.getLogger('forecaster.handler')
mover_logger = logging.getLogger('mover')


class Client(Chainer, metaclass=Singleton):
    """Adapter for trading212api.Client"""

    def __init__(self, bot=None):
        self.mode = self._get_mode()
        super().__init__(successor=bot)
        self.api = trading212api.Client(self.mode)
        self.RESULTS = 0.0  # current net profit
        logger.debug("CLIENT: initied")

    def handle_request(self, event, **kw):
        """pattern function"""
        if event == EVENTS.CHANGE_MODE:
            mode = kw['mode']
            if self.mode != mode:
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

    def login(self, username, password):
        """log in trading212"""
        while True:
            try:
                self.api.login(username, password)
                break
            except trading212api.exceptions.InvalidCredentials as e:
                logger.error("Invalid credentials with {}".format(e.username))
                self.handle_request(EVENTS.MISSING_DATA)
                raise MissingData()
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
        if self.mode == 'demo':
            self.mode = 'live'
        elif self.mode == 'live':
            self.mode = 'demo'
        self.api = trading212api.Client(self.mode)
        self.RESULTS = 0.0
        self.handle_state('swap')
        self.handle_state('init')

    def _get_mode(self):
        try:
            return self._get_data()['mode']
        except (MissingData, KeyError):
            return get_conf()['HANDLER']['mode']

    def _get_data(self):
        """get credentials if exist"""
        try:
            return read_data('data')
        except FileNotFoundError:
            raise MissingData()

    def _auto_login(self):
        """"auto login with credentials"""
        self.login(self.data['username'], self.data['password'])


class SentryClient(raven.Client, metaclass=Singleton):
    """sentry handler to handle exceptions"""

    def __init__(self, *args, **kwargs):
        token = read_tokens()['sentry']
        version = __version__.strip('v')
        env = 'developing'
        super().__init__(dsn=token, release=version, environment=env, *args, **kwargs)
        logger.debug("SENTRY: initied")
