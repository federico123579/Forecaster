# ~~~~ log_summary.py ~~~~
#  forecaster.log_summary
# ~~~~~~~~~~~~~~~~~~~~~~~

from datetime import datetime
import os

import pandas as pd
import numpy as np

from foreanalyzer.cache_optimization import cache_path, save_cache


def get_log_files():
    """get log files and return in order of creation"""
    logs_folder = os.path.join(os.path.dirname(__file__), 'logs')
    # sort files
    sorted_files = sorted([x for x in os.listdir(logs_folder) if 'log.' in x],
                          key=lambda x: tuple(map(int, x.split('.')[-1].split('-'))))
    # insert recent logfile
    if 'logfile.log' in os.listdir(logs_folder):
        sorted_files.append('logfile.log')
    # yield
    for logfile in sorted_files:
        yield os.path.join(logs_folder, logfile)


# ~ * LOG SUMMARY CLASS * ~
class LogRecap(object):
    """summarize logfile"""
    def __init__(self):
        self.market_closed = None

    def _get_attrs(self,line):
        """get attributes from line"""
        if not any(x in line for x in ['DEBUG', 'INFO', 'WARN', 'ERROR']):
            raise ValueError()
        line_seg = line.split(' - ')
        dtm = datetime.fromisoformat(line_seg[0])
        level = line_seg[1]
        origin = line_seg[2]
        text = line_seg[3]
        return [dtm, level, origin, text]

    def check_market_closed(self, line):
        """check if market closed is present in line and return data entry"""
        dtm, _, origin, text = self._get_attrs(line)
        if "market closed" in text.lower() and 'exception' in origin:
            return dtm
    
    def process_market_closed(self, close_dates):
        """process and put a strat and an end date from close dates, return dataframe"""
        close_dates = pd.Series(close_dates)
        first_close = close_dates.iloc[0]
        last_close = close_dates.iloc[-1]
        # check open
        opens = close_dates[(close_dates - close_dates.shift(1)).map(lambda x: x.total_seconds() > 30*60)]
        opens = opens.append(pd.Series((np.nan))).reset_index().drop(columns=['index']).shift(1)[0]
        opens.iloc[0] = first_close
        # check closes
        closes = close_dates[(close_dates.shift(-1) - close_dates).map(lambda x: x.total_seconds() > 30*60)]
        closes = closes.append(pd.Series((np.nan))).reset_index().drop(columns=['index'])[0]
        closes.iloc[-1] = last_close
        # compose
        dates = pd.DataFrame()
        dates['open'] = opens.values
        dates['close'] = closes
        self.market_closed = dates
        return self.market_closed


    def main(self):
        """main command"""
        # get lines of files
        for logfile in get_log_files():
            with open(logfile, 'r') as f:
                data = f.readlines()
            _market_closed = [] # ~ Market
            for line in data:
                try:
                    # check every line and process
                    # ~ Market
                    market_entry = self.check_market_closed(line)
                    if market_entry is not None:
                        _market_closed.append(market_entry)
                except ValueError:
                    continue
        data = {}
        # ~ Market
        data['market'] = self.process_market_closed(pd.Series(_market_closed))
        # save cache
        save_cache(cache_path(['log_summary'], ['result01']), data)
