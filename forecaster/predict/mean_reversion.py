"""
forecaster.predict.mean_reversion
~~~~~~~~~~~~~~

Use a mean reversion for trading.
Use a strategy pattern to work with a yml file.
"""

import logging

#from scipy import stats
import pandas as pd
import numpy as np

from forecaster.predict.utils import AverageTrueRange
from forecaster.enums import ACTIONS

LOGGER = logging.getLogger('forecaster.predict.mean_reversion')


class MeanReversionPredicter(object):
    """predicter"""
    # EDITED IN APLHA2

    def __init__(self, strategy):
        self.multiplier = strategy['multiplier']
        self.period = strategy['period']
        LOGGER.debug("initied MeanReversionPredicter")

    def predict(self, candles):
        """predict if is it worth"""
        # EDITED IN ALPHA2
        # composing the dataframe
        datetimes = [pd.to_datetime(x['timestamp'], unit='s') for x in candles]
        opens = [x['open'] for x in candles]
        closes = [x['close'] for x in candles]
        high = [x['high'] for x in candles]
        low = [x['low'] for x in candles]
        candles_df = pd.DataFrame(data={'datetime': datetimes, 'open': opens,
                                  'close': closes, 'high': high, 'low': low})
        # calculating bolliger bands
        t_price = (candles_df['high'] + candles_df['low'] + candles_df[
            'close']) / 3
        ma_series = t_price.rolling(self.period).mean()
        std_series = t_price.rolling(self.period).apply(np.std, raw=True)
        bol_up = ma_series + self.multiplier * std_series
        bol_dw = ma_series - self.multiplier * std_series
        std_width = (bol_up - bol_dw).rolling(self.period).apply(np.std,
                                                                 raw=True)
        width_series = std_width / std_width.rolling(self.period).mean()
        values = pd.DataFrame(data={'BollBands_up': bol_up,
                                    'BollBands_down': bol_dw,
                                    'BollBands_ma': ma_series,
                                    'BollBands_width': width_series})
        return values
        # linear least-squared regression
        #band = self.get_band(candles)
        #close = [x['close'] for x in candles][-1]
        #diff = close - band  # get diff to display
        #perc = 100 * (close / band - 1)  # get diff to display
        #if close > band:
        #    LOGGER.debug("above bolliger band of {} - {:.2f}%".format(diff, perc))
        #    return ACTIONS.SELL
        #else:
        #    LOGGER.debug("below bolliger band of {} - {:.2f}%".format(diff, perc))
        #    return ACTIONS.BUY

    def get_score(self, candles):
        """get score from band relative"""
        close = [x['close'] for x in candles][-1]
        band = self.get_band(candles)
        return abs(close - band) / close

    def get_band(self, candles):
        """get bolliger band"""
        day_closes = [x['close'] for x in candles]
        moving_average = stats.linregress(range(1, len(day_closes) + 1), day_closes)[1]
        moving_dev = AverageTrueRange(candles)  # deviation function
        band = moving_average + self.mult * moving_dev  # calculate Bolliger Band
        return band
