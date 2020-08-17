# ~~~~ bot.py ~~~~
#  forecaster.bot
# ~~~~~~~~~~~~~~~~

from foreanalyzer.api_handler import APIHandler
from foreanalyzer.console import CliConsole
from foreanalyzer.plot_hanlder import PlotterFactory
from foreanalyzer.utils import read_int_config, write_int_config


USER_ID = "11309135"
PASSWD = "TestTest1."
MODE = "demo"
VOLUME = 0.1

# ~ * DEBUG * ~
def DEBUG(text, level=1):
    CliConsole().debug(text, "forecaster", level)

def INFO(text):
    CliConsole().info(text, "forecaster")


# ~ * BOT RELATED FUNCTIONS * ~
def get_data():
    """get data from plotter"""
    plotter = PlotterFactory['CDSPLT'](
        instruments=['EURUSD'],
        feeders=['XTBF01'],
        timeframe=1800)
    plotter.feed()
    plotter.add_indicator('BBANDS', period=12)
    plotter.add_indicator('SAR', acceleration=5.0)
    return plotter.data['EURUSD']['XTBF01']

def setup_creds():
    """read config and set credentials"""
    config = read_int_config()
    config['credentials']['username'] = USER_ID
    config['credentials']['password'] = PASSWD
    write_int_config(config)


# ~~~ * MAIN BOT * ~~~~
def main():
    # TODO: check if analsys works with XTBApi predict profit
    # TODO: try/except with client logout and keyboard interrupt
    # log foreanalyzer with credentials
    setup_creds()
    data = get_data()
    # override mode with direct control of XTBApi client
    client = APIHandler().api
    client.logout()
    client.login(USER_ID, PASSWD, MODE)
    # TODO: wait right time using client.get_server_time
    # TODO: assert market is open
    # TODO: assert right time
    # TODO: set up a logger
    prev_et = data.iloc[-2]
    curr_et = data.iloc[-1]
    if (prev_et['high'] > prev_et['SAR']) and (curr_et['open'] < curr_et['SAR']):
        # TODO: place short
        client.open_trade(1, 'EURUSD', VOLUME)
    elif (prev_et['low'] < prev_et['SAR']) and (curr_et['open'] > curr_et['SAR']):
        # TODO: place long
        client.open_trade(0, 'EURUSD', VOLUME)


if __name__ == "__main__":
    main()