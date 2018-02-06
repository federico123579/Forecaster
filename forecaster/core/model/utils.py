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
