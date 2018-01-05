# -*- coding: utf-8 -*-

"""
bitgen.model.forex
~~~~~~~~~~~~~~

This module provides the model for predictiong forex trends.
"""

""" TODOS
 - fix tele.py
"""

import json
import requests
import pandas as pd
from bitgen.model.glob import OmniModel, DefaultModel
from bitgen.exceptions import *

# url for updates
URL = ('http://api.fxhistoricaldata.com/indicators?instruments=%s&' +
       'expression=open,high,low,close&item_count=10&format=csv&timeframe=hour')
API_URL = 'https://forex.1forge.com/1.0.1/quotes?pairs=%s&api_key=%s'


class ForexPredict(DefaultModel):
    def __init__(self, obs):
        super().__init__(obs)

    def init_creds(self):
        """save credentials"""
        OmniController().collection['PERS_DATA'].read()
        try:
            self.api_key = OmniController().pers_data['oneforge-api']
        except KeyError:
            raise MissingConfig()

    def update(self, curr):
        """update prices for one currency"""
        self._check_curr(curr)
        url = URL % curr
        api_url = API_URL % (curr, self.api_key)
        dataframe = pd.read_csv(url, header=None)
        values = dataframe.drop([0, 1], axis=1).values
        price = json.loads(requests.get(api_url).content)[0]['price']
        values[0][3] = price  # change close price, more accuracy
        setattr(self, curr, values)  # set values to feed

    def _check_curr(self, curr):
        if curr not in ['EURUSD', 'USDCHF', 'GBPUSD', 'USDJPY']:
            raise ValueError("%s is not acceptable" curr)