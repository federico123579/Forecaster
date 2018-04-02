"""
forecaster.handler
~~~~~~~~~~~~~~

Handle requests and responses from API
"""

import logging
import time

import requests

import raven
import trading212api
from forecaster import __version__
from forecaster.enums import ACTIONS, EVENTS
from forecaster.exceptions import MissingData
from forecaster.patterns import Chainer, Singleton
from forecaster.utils import get_conf, read_data, read_tokens

LOGGER = logging.getLogger('forecaster.handler')
MOVER_LOGGER = logging.getLogger('mover')


class Client(Chainer, metaclass=Singleton):
    """Adapter for trading212api.Client"""

    def __init__(self, bot=None):
        super().__init__(successor=bot)
        self.mode = self._get_mode()
        self.api = trading212api.Client(self.mode)
        self.results = 0.0  # current net profit
        LOGGER.debug("CLIENT: initied")

    @property
    def positions(self):
        return self.api.positions

    @property
    def account(self):
        return self.api.account

    @property
    def funds(self):
        return self.api.account.funds

    def handle_request(self, event, **kw):
        """chainer function"""
        if event == ACTIONS.CHANGE_MODE:
            mode = kw['mode']
            if self.mode != mode:
                LOGGER.info("CLIENT: switching mode from {} to {}".format(self.mode, mode))
                self.swap()
                LOGGER.info("CLIENT: current mode: {}".format(self.mode))
                return self.mode == mode
        else:
            self.pass_request(event, **kw)

    def start(self):
        """start from credentials in data file"""
        try:
            self.data = self._get_data()
        except MissingData:
            self.handle_request(EVENTS.MISSING_DATA)
        self._auto_login()
        LOGGER.debug("CLIENT: started with data")

    def login(self, username, password):
        """log in trading212"""
        while True:
            try:
                self.api.login(username, password)
                self.username = username
                break
            except trading212api.exceptions.InvalidCredentials as e:
                LOGGER.error("Invalid credentials with {}".format(e.username))
                self.handle_request(EVENTS.MISSING_DATA)
            except trading212api.exceptions.LiveNotConfigured:
                LOGGER.error("{} mode not configured".format(self.mode))
                self.handle_request(EVENTS.MODE_FAILURE)
        LOGGER.debug("CLIENT: logged in")

    def open_pos(self, symbol, mode, quantity):
        """open position and handle exceptions"""
        self.refresh()  # renovate sessions
        while True:  # handle exceptions
            try:
                self.api.open_position(mode, symbol, quantity)
                MOVER_LOGGER.info("opened position of {:d} {} on {}".format(quantity, symbol, mode))
                break
            except trading212api.exceptions.PriceChangedException:
                continue
            except trading212api.exceptions.MinQuantityExceeded:
                LOGGER.warning("Minimum quantity exceeded")
                SentryClient().captureException()
                break
            except trading212api.exceptions.MaxQuantityExceeded:
                LOGGER.warning("Maximum quantity exceeded")
                break
            except trading212api.exceptions.MarketClosed:
                LOGGER.warning("Market closed for {}".format(symbol))
                self.handle_request(EVENTS.MARKET_CLOSED, sym=symbol)
                break
            except trading212api.exceptions.NoPriceException:
                LOGGER.warning("NoPriceException caught")
                time.sleep(1)  # waiting 1 second
            except trading212api.exceptions.ProductNotAvaible:
                LOGGER.warning("Product not avaible")
                SentryClient().debug("{} product not avaible".format(symbol))
                SentryClient().captureException()
                break

    def close_pos(self, pos):
        """close position and update results"""
        self.refresh()  # renovate sessions
        while True:
            try:
                self.api.close_position(pos.id)  # close
                MOVER_LOGGER.info("closed position {}".format(pos.id))
                MOVER_LOGGER.info("gain: {:.2f}".format(pos.result))
                break
            except trading212api.exceptions.NoPriceException:
                LOGGER.warning("NoPriceException caught")
                time.sleep(1)  # waiting 1 second
            except ValueError:
                LOGGER.warning("Position not found")
                break
        self.results += pos.result  # update returns
        self.handle_request(EVENTS.CLOSED_POS, pos=pos)

    def close_all(self):
        """close all positions"""
        self.refresh()
        poss = []
        for pos in self.api.account.positions:
            poss.append(pos)
        for pos in poss:  # avoid continue refresh
            self.close_pos(pos)

    def get_last_candles(self, symbol, num, timeframe):
        """get last candles"""
        self.refresh()  # renovate sessions
        candles = self.api.get_historical_data(symbol, num, timeframe)
        prices = [candle['bid'] for candle in candles]
        return prices

    def get_margin(self, symbol, quantity):
        """get margin"""
        return self.api.get_margin(symbol, quantity)

    def refresh(self):
        """refresh the session"""
        try:
            self.api.refresh()
        except trading212api.exceptions.RequestError:
            LOGGER.warning("API unavaible")
            self._auto_login()
            self.api.refresh()
        except requests.exceptions.ConnectionError:
            LOGGER.error("Connection error")
            SentryClient().captureException()
            self.handle_request(EVENTS.CONNECTION_ERROR)

    def swap(self):
        """swap mode"""
        if self.mode == 'demo':
            self.mode = 'live'
        elif self.mode == 'live':
            self.mode = 'demo'
        self.api = trading212api.Client(self.mode)
        self.results = 0.0
        self._auto_login()

    def _get_mode(self):
        """get mode"""
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
        self.breadcrumbs = raven.breadcrumbs
        LOGGER.debug("SENTRY: initied")

    def record(self, text, *args, **kwargs):
        self.breadcrumbs.record(message=text, *args, **kwargs)

    def debug(self, text):
        self.breadcrumbs.record(text, level='debug')

    def info(self, text):
        self.breadcrumbs.record(text, level='info')

    def warning(self, text):
        self.breadcrumbs.record(text, level='warning')

    def error(self, text):
        self.breadcrumbs.record(text, level='error')
