# ~~~~ bot.py ~~~~
#  forecaster.bot
# ~~~~~~~~~~~~~~~~
# TODO: build a log digester to create a report of trades reading logfiles
# TODO: add telegram integration

import logging
import math
import os
import time

import click
from foreanalyzer.api_handler import APIHandler
from foreanalyzer.cache_optimization import cache_path, load_cache, save_cache
from foreanalyzer.plot_hanlder import PlotterFactory
from foreanalyzer.utils import read_int_config, write_int_config
import XTBApi.exceptions as xtbexc

from forecaster.console import ForeCliConsole
import forecaster.exceptions as exc


# ~ * DEBUG * ~
def DEBUG(text, level=1):
    ForeCliConsole().debug(text, "bot", level)

def INFO(text):
    ForeCliConsole().info(text, "bot")

def WARN(text):
    ForeCliConsole().warn(text, "bot")

def ERROR(text):
    ForeCliConsole().error(text, "bot")


def measure_time(text_to_dispaly, func, *args, **kwargs):
    """measure time of execution and log"""
    start = time.time()
    res = func(*args, **kwargs)
    sec = time.time() - start
    DEBUG(f"{text_to_dispaly} took {sec:.2f}s", level=2)
    return res


# ~ * BOT RELATED OBJECTS * ~
class Account(object):
    """account object"""
    def __init__(self, client):
        self.balance = None
        self.client = client
        self.trades = client.trade_rec
        self.opentrade_ids = []
        self.order_ids = []

    def time(self):
        """return server time"""
        return self.client.get_server_time()

    def update_balance(self):
        """update account balance"""
        self.balance = self.client.get_margin_level()['balance']
        return self.balance

    def update_trades(self):
        """update trades in account"""
        self.client.update_trades()
        self.opentrades_dict = {x.opentrade_id: x for _, x in self.trades.items()}
        _to_remove = []
        for opentrade_id in self.opentrade_ids:
            if opentrade_id not in [x for x in self.opentrades_dict.keys()]:
                _to_remove.append(opentrade_id)
        for x in _to_remove:
            self.opentrade_ids.remove(x)
            DEBUG(f"{opentrade_id} not found in current trades - removed")
        self.order_ids = [self.opentrades_dict[x].order_id for x in self.opentrade_ids]
        return self.order_ids


class Instrument(object):
    """instrument dataspace"""
    def __init__(self, instrument, client):
        self.name = instrument
        self.client = client
        self._last_data = None
        self._last_updated = None
        self.ask_price = None
        self.bid_price = None
        self.contract_size = None
        self.leverage = None
        self.lot_min = None
        self.lot_max = None

    def get_info(self):
        """get info from server"""
        self._last_data = self.client.get_symbol(self.name)
        self._last_updated = time.time()
        self.ask_price = self._last_data['ask']
        self.bid_price = self._last_data['bid']
        self.contract_size = self._last_data['contractSize']
        self.leverage = self._last_data['leverage'] / 100
        self.lot_min = self._last_data['lotMin']
        self.lot_max = self._last_data['lotMax']
        self.lot_step = self._last_data['lotStep']
        return self
    
    def get_volume(self, money_to_convert):
        """convert fixed amount of money to vol"""
        float_vol = (money_to_convert / self.leverage) / self.contract_size
        digits = len(str(self.lot_step).split('.')[1])
        if float_vol < self.lot_min:
            raise ValueError("volume too small")
        elif float_vol > self.lot_max:
            WARN("volume too high, reset to max")
        return round(float_vol, digits)
        

# ~~~ * MAIN BOT * ~~~~
class ForeBot():
    """main class"""
    def __init__(self, username, password, mode='demo', instrument='EURUSD',
                 volume_percentage=0.4, timeframe=1800):
        self._last_candle_tmstp = 0
        self._status = {
            'setup': 0, # 0 not set up - 1 set up
            'check_mode': 0 # 0 check open - 1 check close
        }
        self.account = None # account object above
        self.client = None # XTBApi client
        self.data = None # data from XTBApi feeder from foreanalyzer plotter
        self.instrument = None # instrument object above
        self.instrument_name = instrument
        self.mode = mode
        self.password = password
        self.plotter = None
        self.timeframe = timeframe
        self.user_id = username
        self.vol_perc = volume_percentage # percentage * account balance = money spent on new trans margin
        DEBUG(f"Bot set - user: {self.user_id} - mode: {self.mode} - instr: {self.instrument_name}")
            
    def _check_setup(self):
        """check if bot status is set up"""
        if self._status['setup'] != 1:
            raise exc.BotNotSetUp()
        
    def _get_data(self):
        """get data from plotter"""
        self._check_setup()
        self.plotter = PlotterFactory['CDSPLT'](
            instruments=[self.instrument.name],
            feeders=['XTBF01'],
            timeframe=self.timeframe,
            time_past=3600*24*14)
        _xtbapi_level = logging.getLogger("XTBApi").getEffectiveLevel()
        logging.getLogger("XTBApi").setLevel(logging.WARNING)
        DEBUG("turned off XTBApi logger", 3)
        DEBUG("feeding data")
        self.plotter.feed()
        logging.getLogger("XTBApi").setLevel(_xtbapi_level)
        DEBUG("turned on XTBApi logger", 3)
        self.plotter.add_indicator('BBANDS', period=30)
        self.plotter.add_indicator('SMA', period=50)
        self.data = self.plotter.data[self.instrument.name]['XTBF01']
        return self.data
    
    def _setup_creds(self):
        """read config and set credentials"""
        config = read_int_config()
        config['credentials']['username'] = self.user_id
        config['credentials']['password'] = self.password
        write_int_config(config)
        DEBUG("credentials config saved")

    def check_close(self, candle):
        """check if close conditions are met"""
        # TODO: add better logging
        # TODO: add efficient stop loss
        self._check_setup()
        current_price = self.instrument.get_info().ask_price
        # this will consist always of one transaction for this algo
        order_id = self.account.order_ids[0]
        mode = self.account.trades[order_id].mode
        # check close short
        if (mode == 'sell') and (current_price < candle['BBANDS_30_md']):
            INFO(f"CLOSE SHORT SIGNAL")
            self.close_trade(order_id)
        # check close long
        elif (mode == 'buy') and (current_price > candle['BBANDS_30_md']):
            INFO(f"CLOSE LONG SIGNAL")
            self.close_trade(order_id)

    def check_market(self):
        """check if market is open"""
        # TODO: check the error generated with market closed
        market_open = self.client.check_if_market_open(
            [self.instrument.name])[self.instrument_name]
        if not market_open: # wait until market opens
            raise exc.MarketClosed()

    def check_open(self, candle):
        """check if conditions are met for open positions, get candle from ForeBot.get_candle()"""
        # TODO: add better logging
        self._check_setup()
        current_price = self.instrument.get_info().ask_price
        # open short
        if (current_price > candle['BBANDS_30_up']) and (candle['close'] < candle['SMA_50']):
            DEBUG(f"entering on short")
            self.open_trade('sell')
        # open long
        elif (current_price < candle['BBANDS_30_dw']) and (candle['close'] > candle['SMA_50']):
            DEBUG(f"entering on long")
            self.open_trade('buy')

    def close_trade(self, generic_id, type_of_id=0):
        """close trade with two different ids (order, opentrade)"""
        # TODO: add better logging
        if self._status['check_mode'] != 1:
            ERROR("tried to close order with no orders")
            return None
        if (generic_id not in self.account.opentrade_ids) and (
                generic_id not in self.account.order_ids):
            WARN(f"order {generic_id} of type {type_of_id} alredy closed")
        if type_of_id in [0, 'order']:
            order_id = generic_id
        elif type_of_id in [1, 'opentrade']:
            order_id = self.account.opentrades_dict[generic_id].order_id
        res = self.client.close_trade(order_id)
        self._status['check_mode'] = 0
        return res
    
    def get_candle(self):
        """check if a new candle is needed a return data"""
        # TODO: add better logging
        # minutes from last close of a stable candle
        def _get_m_last_close():
            return math.floor((time.time() - self._last_candle_tmstp) / 60) - 30
        if _get_m_last_close() < 30: # return old candle
            return self.data.iloc[-2]
        else: # new candle requested
            self.check_market()
            n = 0 # log tries
            while _get_m_last_close() >= 30:
                DEBUG(f"trying to get new candle: try #{n}")
                entry = measure_time("func ForeBot._get_data", self._get_data).iloc[-2]
                self._last_candle_tmstp = entry.name.to_pydatetime().timestamp()
                n += 1
                if n >= 2:
                    WARN(f"candle is late - try #{n}")
            return entry

    def main_loop(self):
        """turn on the main loop of check signals"""
        # TODO: try/except with client logout and keyboard interrupt
        try:
            candle = self.get_candle()
            if self._status['check_mode'] == 0:
                self.check_open(candle)
            elif self._status['check_mode'] == 1:
                self.check_close(candle)
        except exc.MarketClosed:
            time.sleep(1)
        except Exception as e:
            pass # TODO: add sentry integration and control

    def open_trade(self, mode):
        """open a new transaction and calc volume"""
        # TODO: add better logging
        # TODO: add procedures to control exceptions and add exception
        #       check status
        if self._status['check_mode'] != 0:
            ERROR(f"tried to open trade with a trade alredy opened") # FIXME
            return self.account.opentrade_ids[0]
        self._check_setup()
        self.instrument.get_info()
        self.account.update_balance()
        trade_volume = self.account.balance * self.vol_perc
        if mode in [0, 'buy']:
            response = self.client.open_trade(
                0, self.instrument.name, self.instrument.get_volume(trade_volume))
        elif mode in [1, 'sell']:
            response = self.client.open_trade(
                1, self.instrument.name, self.instrument.get_volume(trade_volume))
        else:
            raise ValueError(f"mode {mode} not accepted")
        opentrade_id = response['order']
        if opentrade_id not in self.account.opentrade_ids:
            self.account.opentrade_ids.append(opentrade_id)
        self._status['check_mode'] = 1
        return opentrade_id

    def setup(self):
        """set up all components and config, set up xtb api client"""
        self._setup_creds()
        APIHandler().setup(self.mode)
        self.client = APIHandler().api
        self.instrument = Instrument(self.instrument_name, self.client)
        self.account = Account(self.client)
        self._status['setup'] = 1 # bot set up
        DEBUG("Bot and xtb client set up")


# ~~~ * MAIN COMMAND * ~~~~
@click.command()
@click.option('-v', '--verbose', count=True, default=0, show_default=True)
def main(verbose):
    ForeCliConsole().verbose = verbose

@main.command()
def run():
    bot = ForeBot(
        username='11361612',
        password='TestTest1.',
        telegram_token='548272219:AAHo1jOMFNJ5A3TzPLhzqwm-qBCwEYVbJ7g',
        mode='demo',
        instrument='EURUSD',
        volume_percentage=0.4)
    try: # TODO: try anc catch all exceptions
        bot.setup() # set up the bot, starts the api client
    except xtbexc.NoInternetConnection:
        ERROR("no internet connection")
        return
    start = time.time()
    while (time.time() - start) < 30:
        bot.main_loop()


main()