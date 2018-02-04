# -*- coding: utf-8 -*-

"""
forecaster.model.forex
~~~~~~~~~~~~~~

This module provides the model for predictiong forex trends.
"""

# TODO:
# - fix tele.py

import time
import os.path
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
from forecaster.glob import CURR
from forecaster.core.model.glob import *
from forecaster.exceptions import *
from forecaster.core.model.exceptions import *

# logging
import logging
logger = logging.getLogger('forecaster.model.forex')


class ForexPredict(DefaultModel):
    def __init__(self, obs):
        super().__init__(obs)
        self.curr = {}
        self._init_currencies()
        self.models = {}

    def init_model(self):
        """load model"""
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'model.h5')
        if not os.path.isfile(path):
            raise MissingModel()
        self.model = load_model(path)

    def predict(self, curr):
        self.update(curr)
        prediction = self.model.predict(np.expand_dims(self.curr[curr]['feed'], axis=0))
        logger.debug("predicted")
        return prediction[0]

    def update(self, curr):
        """update prices for one currency"""
        # OPTIMIZE
        self._check_curr(curr)
        # get candles
        self.notify_observers(event="historical_data", data={'name': curr, 'limit': 24})
        candles = []
        for candle in self.hist:  # create readable candles
            op = candle['bid']['open']
            mx = candle['bid']['high']
            mn = candle['bid']['low']
            cl = candle['bid']['close']
            candles.append([op, mx, mn, cl])
        candles = np.array(candles)  # convert in a numpy array
        # get smas
        smas = np.array([self._get_sma(x, 14) for x in self._group(
            candles.transpose()[3], 14)][-10:])
        values = np.c_[candles[-10:], smas[:, None]]  # combine with smas
        self.curr[curr]['feed'] = self._scale(values)  # set values to feed
        logger.debug("updated values")

    def _group(self, values, hours):
        data_grouped = []
        for i in range(len(values)-hours):
            data_grouped.append(values[i:i+hours])
        return np.array(data_grouped)

    def _scale(self, arr):
        scaler = MinMaxScaler(feature_range=(-1, 1))
        scaler.fit(arr)
        return np.array(scaler.transform(arr))

    def _get_sma(self, values, periods):
        return sum(values)/periods

    def _init_currencies(self):
        """init currencies in dict curr"""
        for cur in CURR:
            if not self.curr.get(cur):
                self.curr[cur] = {}
                self.curr[cur]['feed'] = []

    def _check_curr(self, curr):
        if curr not in CURR:
            raise ValueError("%s is not acceptable" % curr)
