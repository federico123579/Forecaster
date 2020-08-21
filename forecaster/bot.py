# ~~~~ bot.py ~~~~
#  forecaster.bot
# ~~~~~~~~~~~~~~~~

import logging
import math
import os.path
import time

import click
from foreanalyzer.api_handler import APIHandler
from foreanalyzer.cache_optimization import cache_path, load_cache, save_cache
from foreanalyzer.plot_hanlder import PlotterFactory
from foreanalyzer.utils import read_int_config, write_int_config

from forecaster.console import ForeCliConsole
from forecaster.exceptions import BotNotSetUp


# ~ * DEBUG * ~
def DEBUG(text, level=1):
    ForeCliConsole().debug(text, "bot", level)

def INFO(text):
    ForeCliConsole().info(text, "bot")

def WARN(text):
    ForeCliConsole().warn(text, "bot")


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
        self._status = 0 # 0 not set up - 1 set up
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
        if self._status != 1:
            raise BotNotSetUp()
        
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

    def check_open(self, candle):
        """check if conditions are met for open positions, get candle from ForeBot.get_candle()"""
        # TODO: add better logging
        # TODO: check if candle is updated
        # TODO: check updated time and wait or return none
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
        if (generic_id not in self.account.opentrade_ids) and (
                generic_id not in self.account.order_ids):
            WARN(f"order {generic_id} of type {type_of_id} alredy closed")
        if type_of_id in [0, 'order']:
            order_id = generic_id
        elif type_of_id in [1, 'opentrade']:
            order_id = self.account.opentrades_dict[generic_id].order_id
        return self.client.close_trade(order_id)
    
    def get_candle(self):
        """check if a new candle is needed a return data"""
        # TODO: add better logging
        # minutes from last close of a stable candle
        def _get_m_last_close():
            return math.floor((time.time() - self._last_candle_tmstp) / 60) - 30
        if _get_m_last_close() < 30: # return old candle
            return self.data.iloc[-2]
        else: # new candle requested
            market_open = self.client.check_if_market_open(
                self.instrument.name)[self.instrument_name]
            if not market_open: # wait until market opens
                # TODO: wait until market opens
                WARN(f"Market Closed") # FIXME
            else: # market is open
                n = 0 # log tries
                while _get_m_last_close() >= 30:
                    DEBUG(f"trying to get new candle: try #{n}")
                    entry = measure_time("func ForeBot._get_data", self._get_data).iloc[-2]
                    self._last_candle_tmstp = entry.name.to_pydatetime().timestamp()
                    n += 1
                return entry

    def open_trade(self, mode):
        """open a new transaction and calc volume"""
        # TODO: add better logging
        self._check_setup()
        self.instrument.get_info()
        self.account.update_balance()
        trade_volume = self.account.balance * self.vol_perc
        if mode in [0, 'buy']:
            response = self.client.open_trade( # TODO: register tran_id
                0, self.instrument.name, self.instrument.get_volume(trade_volume))
        elif mode in [1, 'sell']:
            response = self.client.open_trade( # TODO: register tran_id
                1, self.instrument.name, self.instrument.get_volume(trade_volume))
        else:
            raise ValueError(f"mode {mode} not accepted")
        opentrade_id = response['order']
        if opentrade_id not in self.account.opentrade_ids:
            self.account.opentrade_ids.append(opentrade_id)
        return opentrade_id

    def setup(self):
        """set up all components and config, set up xtb api client"""
        self._setup_creds()
        APIHandler().setup(self.mode)
        self.client = APIHandler().api
        self.instrument = Instrument(self.instrument_name, self.client)
        self.account = Account(self.client)
        self._status = 1 # bot set up
        DEBUG("Bot and xtb client set up")


        ## TODO: try/except with client logout and keyboard interrupt
        ## log foreanalyzer with credentials
        #filepath = cache_path(['forecaster'], ['XTBApi', '1908'])
        #if os.path.isfile(filepath): # FIXME
            #DEBUG("cache found")
            #data = load_cache(filepath)
            #APIHandler().setup()
        #else:
            #DEBUG("cache not found")
            #setup_creds()
            #DEBUG("write credentials config")
            #data = get_data(INSTRUMENT)
            #save_cache(filepath, data)
        ## override mode with direct control of XTBApi client
        #client = APIHandler().api
        #DEBUG("logging out", 3)
        #DEBUG("try to log in", 3)
        #client.login(USER_ID, PASSWD, MODE)
        #DEBUG(f"client override with credentials and mode {MODE}")
        ## TODO: wait right time using client.get_server_time
        ## TODO: assert market is open
        ## TODO: assert right time
        #prev_et = data.iloc[-2] # -1 takes the last candle which is updated every second
        #instr = Instrument(INSTRUMENT, client).get_info()
        #new_trade_vol = client.get_margin_level()['balance'] * VOL_PERC
        ## short
        #if (instr.ask_price > prev_et['BBANDS_30_up']) and (prev_et['close'] < prev_et['SMA_50']):
            #client.open_trade(1, instr.name, instr.get_volume(new_trade_vol))
        ## long
        #elif (instr.ask_price < prev_et['BBANDS_30_dw']) and (prev_et['close'] > prev_et['SMA_50']):
            #client.open_trade(0, instr.name, instr.get_volume(new_trade_vol))


# ~~~ * MAIN COMMAND * ~~~~
@click.command()
@click.option('-v', '--verbose', count=True, default=0, show_default=True)
def main(verbose):
    ForeCliConsole().verbose = verbose
    USERNAME = '11361612'
    PASSWORD = 'TestTest1.'
    MODE = 'demo'
    INSTRUMENT = 'EURUSD'
    VOLUME_PERCENTAGE = 0.1
    bot = ForeBot(USERNAME, PASSWORD, MODE, INSTRUMENT, VOLUME_PERCENTAGE)
    bot.setup() # set up the bot, starts the api client
    start = time.time()
    while time.time() - start < 60:
        pr = bot.instrument.get_info().ask_price
        DEBUG(f"price: {pr}")
    for i in range(15):
        candle = bot.get_candle()
        bot.check_open(candle)
        DEBUG(f"{i} - got candle {candle.name}")
    pass


main()