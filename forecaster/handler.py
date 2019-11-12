"""
forecaster.handler
~~~~~~~~~~~~~~

Handle requests and responses from API
"""

import logging
import time
from datetime import datetime

import requests

import raven
import XTBApi.api
import XTBApi.exceptions
from forecaster import __version__
from forecaster.enums import ACTIONS, EVENTS
from forecaster.exceptions import MissingData
from forecaster.patterns import Chainer, Singleton
from forecaster.utils import get_conf, read_data, read_tokens

LOGGER = logging.getLogger('forecaster.handler')
MOVER_LOGGER = logging.getLogger('mover')


class Client(Chainer, metaclass=Singleton):
    """Adapter for Client"""

    def __init__(self, bot=None):
        super().__init__(successor=bot)
        self.mode = self._get_mode()
        self.api = XTBApi.api.Client()
        self.username = str
        self.results = 0.0  # current net profit
        LOGGER.debug("CLIENT: initied")

    @property
    def positions(self):
        trans_reg = self.api.update_trades()
        # TODO: fix trading212
        return self.api.positions

    @property
    def account(self):
        # TODO: fix trading212
        return self.api.account

    @property
    def funds(self):
        return self.api.get_margin_level()['balance']

    @property
    def balance_results(self):
        return self.api.get_margin_level()['balance'] - \
               self.api.get_margin_level()['equity']

    def handle_request(self, event, **kw):
        """chainer function"""
        if event == ACTIONS.CHANGE_MODE:
            mode = kw['mode']
            if self.mode != mode:
                LOGGER.info("CLIENT: switching mode from {} to {}".format(
                    self.mode, mode))
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
                self.api.login(username, password, mode=self.mode)
                self.username = username
                break
            except XTBApi.exceptions.CommandFailed as e:
                LOGGER.error("Command Failed: probably invalid credentials "
                             "with {}".format(username))
                self.handle_request(EVENTS.MISSING_DATA)
        # TODO: fix trading212
            except trading212api.exceptions.LiveNotConfigured:
                LOGGER.error("{} mode not configured".format(self.mode))
                self.handle_request(EVENTS.MODE_FAILURE)
        LOGGER.debug("CLIENT: logged in")

    def open_pos(self, symbol, mode, quantity):
        """open position and handle exceptions"""
        self.refresh()  # renovate sessions
        while True:  # handle exceptions
            try: 
        # TODO: fix trading212
                self.api.open_position(mode, symbol, quantity)
                MOVER_LOGGER.info("opened position of {:d} {} on {}".format(
                    quantity, symbol, mode))
                break 
        # TODO: fix trading212
            except trading212api.exceptions.PriceChangedException:
                continue 
        # TODO: fix trading212
            except trading212api.exceptions.MinQuantityExceeded:
                LOGGER.warning("Minimum quantity exceeded")
                SentryClient().captureException()
                break 
        # TODO: fix trading212
            except trading212api.exceptions.MaxQuantityExceeded:
                LOGGER.warning("Maximum quantity exceeded")
                break 
        # TODO: fix trading212
            except trading212api.exceptions.MarketClosed:
                LOGGER.warning("Market closed for {}".format(symbol))
                self.handle_request(EVENTS.MARKET_CLOSED, sym=symbol)
                break 
        # TODO: fix trading212
            except trading212api.exceptions.NoPriceException:
                LOGGER.warning("NoPriceException caught")
                time.sleep(1)  # waiting 1 second 
        # TODO: fix trading212
            except trading212api.exceptions.ProductNotAvaible:
                LOGGER.warning("Product not avaible")
                SentryClient().debug("{} product not avaible".format(symbol))
                SentryClient().captureException()
                break

    def close_pos(self, pos_id):
        """close position and update results"""
        self.refresh()  # renovate sessions
        while True:
            try: 
                self.api.close_trade(pos_id)  # close
                MOVER_LOGGER.info("closed position {}".format(pos_id))
                pos = self.api.trade_rec[pos_id]
                MOVER_LOGGER.info("gain: {:.2f}".format(pos.actual_profit))
                break 
        #    except trading212api.exceptions.NoPriceException:
        #        LOGGER.warning("NoPriceException caught")
        #        time.sleep(1)  # waiting 1 second
            except ValueError:
                LOGGER.warning("Position not found")
                break
        self.results += pos.actual_profit  # update returns
        self.handle_request(EVENTS.CLOSED_POS, pos=pos)

    def close_all(self):
        """close all positions"""
        self.refresh()
        self.api.update_trades()
        results = [trans_id.actual_profit for trans_id in
                   self.api.trade_rec.items()].sum()
        self.api.close_all_trades()
        self.results += results
        self.handle_request(EVENTS.CLOSED_ALL_POS, results=results)

    def get_last_candles(self, symbol, timeframe, num):
        """get last candles"""
        # EDITED IN ALPHA2
        self.refresh()  # renovate sessions 
        candles = self.api.get_lastn_candle_history(symbol, timeframe, num)
        return candles

    def get_margin(self, symbol, quantity):
        """get margin""" 
        # TODO: fix trading212
        return self.api.get_margin(symbol, quantity)

    def refresh(self):
        # EDITED IN ALPHA2
        pass
    #    """refresh the session"""
    #    n_err = 0
    #    while True:
    #        try:
    #            self.api.ping()
    #            break
    #        except Exception as e:
    #            LOGGER.warning(f"API unavaible: {e}")
    #            try:
    #                self._auto_login()
    #                self.api.refresh()
    #            except Exception as e:
    #                LOGGER.error(e)
    #                raise e
    #        # TODO: fix trading212
    #        except requests.exceptions.ConnectionError:
    #            LOGGER.error("Connection error")
    #            SentryClient().captureException()
    #            n_err += 1
    #            if n_err < 6:
    #                LOGGER.warning("reconnection #%s" % n_err)
    #                time.sleep(1)  # sleep one second and cycle again
    #                continue
    #            self.handle_request(EVENTS.CONNECTION_ERROR)
    #            break

    def swap(self):
        """swap mode"""
        if self.mode == 'demo':
            self.mode = 'live'
        elif self.mode == 'live':
            self.mode = 'demo' 
        # TODO: fix trading212
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

    # ADDED IN ALPHA2
    def check_if_market_open(self, list_of_symbol):
        return self.api.check_if_market_open(list_of_symbol)

    def get_position_len(self):
        return len(self.api.get_trades(True))

    #def get_sec_until_market_opens(self, list_of_symbols):
    #    # ADDED IN ALPHA2
    #    _td = datetime.today()
    #    actual_tmsp = _td.hour * 3600 + _td.minute * 60 + _td.second
    #    td_dayofweek = _td.isoweekday()
    #    trading_hours = self.api.get_trading_hours(list_of_symbols)
    #    sec_to_open_dict = {}
    #    for symbol in trading_hours:
    #        # DOES NOT CONSIDER MORE THAN ONE INTERVAL IN A DAY
    #        fmt_hours = {x['day']: [x['fromT'], x['toT']] for x in symbol[
    #            'trading']}
    #        tmp_dayofweek = td_dayofweek
    #        days = 0
    #        while 1:
    #            # check if tmp_dayofweek is greater than 7
    #            if tmp_dayofweek > 7:
    #                tmp_dayofweek = 1
    #            # check if not listed
    #            if tmp_dayofweek not in fmt_hours.keys():
    #                tmp_dayofweek += 1
    #                days += 1
    #                continue
    #            # check if in time
    #            td_hours = fmt_hours[tmp_dayofweek]
    #            if days > 0:
    #                sec_to_open_dict[symbol['symbol']] = days * 86400 + \
    #                    td_hours[0] - actual_tmsp
    #                break
    #            elif td_hours[0] <= actual_tmsp <= td_hours[1]:
    #                sec_to_open_dict[symbol['symbol']] = 0
    #                break
    #            elif actual_tmsp <= td_hours[0]:
    #                sec_to_open_dict[symbol['symbol']] = td_hours[0] - \
    #                    actual_tmsp
    #                break
    #            else:
    #                tmp_dayofweek += 1
    #                days += 1
    #                continue
    #    return sec_to_open_dict


class SentryClient(raven.Client, metaclass=Singleton):
    """sentry handler to handle exceptions"""

    def __init__(self, *args, **kwargs):
        token = read_tokens()['sentry']
        version = __version__.strip('v')
        env = 'developing'
        super().__init__(dsn=token, release=version, environment=env, *args,
                         **kwargs)
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
