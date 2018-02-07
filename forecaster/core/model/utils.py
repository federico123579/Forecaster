# -*- coding: utf-8 -*-

"""
forecaster.core.model.utils
~~~~~~~~~~~~~~

This module provides utils to the model.
"""

import numpy as np
from sklearn.preprocessing import MinMaxScaler

# logging
import logging
logger = logging.getLogger('forecaster.model.utils')


def group(values, periods):
    data_grouped = []
    for i in range(len(values)-periods):
        data_grouped.append(values[i:i+periods])
    return np.array(data_grouped)


def scale(values):
    scaler = MinMaxScaler(feature_range=(-1, 1))
    scaler.fit(values)
    return np.array(scaler.transform(values))


def sma(values, periods):
    return sum(values)/periods


def rsi(values, period):
    rsi = []
    for i in range(len(values)-period):
        gains = 0.0
        losses = 0.0
        window = values[i:i+period+1]
        for year_one, year_two in zip(window, window[1:]):
            diff = year_two - year_one

            if diff > 0:
                gains += diff
            else:
                losses += abs(diff)
        # Check if `losses` is zero. If so, `100/(1 + RS)` will practically be 0.
        if not losses:
            rsi.append(100.00)
        else:
            rsi.append(round(100 - (100 / (1 + gains / losses)), 2))
    return rsi
