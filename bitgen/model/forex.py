# -*- coding: utf-8 -*-

"""
bitgen.model.forex
~~~~~~~~~~~~~~

This module provides the model for predictiong forex trends.
"""

# TODO:
# - fix tele.py

import os.path
import json
import requests
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
from bitgen.model.glob import OmniModel, DefaultModel
from bitgen.exceptions import *
from bitgen.model.exceptions import *

# logging
import logging
logger = logging.getLogger('bitgen.model.forex')


# url for updates
URL = ('http://api.fxhistoricaldata.com/indicators?instruments=%s&' +
       'expression=open,high,low,close&item_count=%d&format=csv&timeframe=hour')
API_URL = 'https://forex.1forge.com/1.0.1/quotes?pairs=%s&api_key=%s'


class ForexPredict(DefaultModel):
    def __init__(self, obs):
        super().__init__(obs)
        self.curr = {}
        self.models = {}

    def _group(self, values, hours):
        data_grouped = []
        for i in range(len(values)-hours):
            data_grouped.append(values[i:i+hours])
        return np.array(data_grouped)

    def _scale(self, arr):
        # scale
        scaler = MinMaxScaler(feature_range=(-1, 1))
        scaler.fit(arr)
        return np.array(scaler.transform(arr))

    def _get_sma(self, values, periods):
        return sum(values)/periods

    def init_creds(self):
        """save credentials"""
        OmniModel().update()
        try:
            self.api_key = OmniModel().pers_data['oneforge-api']
        except KeyError:
            raise MissingConfig()

    def init_model(self, hours):
        """load model"""
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data',
                            'model_%d_hours.h5' % hours)
        if not os.path.isfile(path):
            raise MissingModel()
        self.models[hours] = load_model(path)

    def predict(self, curr, hours):
        self.update(curr, hours)
        prediction = self.models[hours].predict(np.expand_dims(self.curr[curr], axis=0))
        logger.debug("predicted with %d hours" % hours)
        return prediction[0]

    def update(self, curr, hours):
        """update prices for one currency"""
        self._check_curr(curr)
        # get prices
        url = URL % (curr, hours+14)
        api_url = API_URL % (curr, self.api_key)
        dataframe = pd.read_csv(url, header=None)
        dataframe = dataframe.iloc[::-1]
        # get smas
        dataframe_vals = dataframe.drop([0, 1], axis=1).values
        smas = np.array([self._get_sma(x, 14) for x in self._group(
            dataframe_vals.transpose()[3], 14)][-hours:])
        prices = dataframe_vals[-(hours-1):]
        price = json.loads(requests.get(api_url).content)[0]['price']
        # change close price, more accuracy  # OPTIMIZE
        last_row = np.array([prices[-1][0], prices[-1][1], prices[-1][2], price])[None, :]
        prices = np.r_[prices, last_row]
        # combine
        values = np.c_[prices, smas[:, None]]
        self.curr[curr] = self._scale(values)  # set values to feed
        logger.debug("updated values")

    def _check_curr(self, curr):
        if curr not in ['EURUSD', 'USDCHF', 'GBPUSD', 'USDJPY', 'USDCAD']:
            raise ValueError("%s is not acceptable" % curr)
