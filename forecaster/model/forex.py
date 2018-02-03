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
import json
import requests
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
from forecaster.glob import CURR
from forecaster.model.glob import *
from forecaster.exceptions import *
from forecaster.model.exceptions import *

# logging
import logging
logger = logging.getLogger('forecaster.model.forex')


# url for updates
URL = ('http://api.fxhistoricaldata.com/indicators?instruments=%s&' +
       'expression=open,high,low,close&item_count=%d&format=csv&timeframe=hour')
API_URL = 'https://forex.1forge.com/1.0.1/quotes?pairs=%s&api_key=%s'


class ForexPredict(DefaultModel):
    def __init__(self, obs):
        super().__init__(obs)
        self.active = OmniModel().events['UPDATE']
        self.curr = {}
        self.models = {}

    def init_creds(self):
        """save credentials"""
        OmniModel().update()
        try:
            self.api_key = OmniModel().pers_data['oneforge-api']
        except KeyError:
            raise MissingConfig()

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
        # get prices
        url = URL % (curr, 10+14)
        dataframe = pd.read_csv(url, header=None)
        dataframe = dataframe.iloc[::-1]
        # get smas
        dataframe_vals = dataframe.drop([0, 1], axis=1).values
        smas = np.array([self._get_sma(x, 14) for x in self._group(
            dataframe_vals.transpose()[3], 14)][-10:])
        values_calc = self.curr[curr]['values'][-10:]
        self.update_prices()
        if len(values_calc) == 0:  # change close price, more accuracy  # OPTIMIZE
            prices = dataframe_vals[-(10-1):]
            price = self.curr[curr]['prices'][-1]
            last_rows = np.array([prices[-1][0], prices[-1][1], prices[-1][2], price])[None, :]
        else:  # change with recorded data
            prices = dataframe_vals[-(10-len(values_calc)):]
            last_rows = np.array(values_calc)
        prices = np.r_[prices, last_rows]  # combine last rows
        values = np.c_[prices, smas[:, None]]  # combine with smas
        self.curr[curr]['feed'] = self._scale(values)  # set values to feed
        logger.debug("updated values")

    def update_values(self):
        """thread updater values"""
        while self.active.is_set():
            start = time.time()
            for curr in CURR:
                prices = self.curr[curr]['prices']
                self.curr[curr]['values'].append(self.calc_vals(prices))
                prices.clear()
            logger.debug("updated values")
            time.sleep(max(0, UPDATE_VALUES_TIME - (time.time() - start)))

    def update_prices(self):
        """thread update every price of exchange rates"""
        api_url = API_URL % (','.join(CURR), self.api_key)
        while self.active.is_set():
            start = time.time()
            values = json.loads(contentrequests.get(api_url).content)
            for curr in values:
                records = self.curr[curr['symbol']]
                records['prices'].append(curr['price'])
            logger.debug("updated prices")
            time.sleep(max(0, UPDATE_PRICES_TIME - (time.time() - start)))

    def calc_vals(self, prices):
        """calculate open, max, min and close prices from records"""
        for curr in CURR:
            op = prices[0]
            mx = max(prices)
            mn = min(prices)
            cl = prices[-1]
            return [op, mx, mn, cl]

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
                self.curr[cur]['prices'] = []
                self.curr[cur]['values'] = []
                self.curr[cur]['feed'] = []

    def _check_curr(self, curr):
        if curr not in CURR:
            raise ValueError("%s is not acceptable" % curr)
