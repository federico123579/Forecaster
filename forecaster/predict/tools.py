#!/usr/bin/env python

"""
forecaster.predict.tools
~~~~~~~~~~~~~~

Collection of tools need to calculate indexes.
"""

import numpy as np
from sklearn.preprocessing import MinMaxScaler


def sma(values, periods):
    """Simple Moving Average"""
    return sum(values) / periods


def rsi(values, periods):
    """Relative Strenght of Index"""
    gains = 0
    losses = 0
    for val1, val2 in zip(values, values[1:]):
        diff = val2 - val1
        if diff > 0:
            gains += diff
        else:
            losses += abs(diff)
    if not losses:
        ind = 100
    else:
        ind = 100 - (100 / (1 + gains / losses))
    if ind >= 70:
        return 1
    elif ind <= 30:
        return -1
    else:
        return 0


def stochastic(values):
    """Stochastic Oscillator"""
    ks = []
    for x in [4, 8, 12]:
        portion = values[x - 4:x]
        low = min(portion)
        high = max(portion)
        k = 100 * (portion[-1] - low) / (high - low)
        ks.append(k)
    kk = np.mean(ks)
    if kk >= 80:
        return 1
    elif kk <= 20:
        return -1
    else:
        return 0


def scale(values):
    scaler = MinMaxScaler(feature_range=(-1, 1))
    scaler.fit(values)
    return np.array(scaler.transform(values))
