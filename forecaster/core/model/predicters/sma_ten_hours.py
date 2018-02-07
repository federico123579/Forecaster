#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
forecaster.core.model.predicters.sma_ten_hours
~~~~~~~~~~~~~~

Neural network that predict trend using 10 hours values and sma.
"""

import os.path
import pandas as pd
import numpy as np
from keras.models import Sequential, load_model
from keras.layers import Dense, Activation, LSTM
from forecaster.core.model.utils import *
from forecaster.glob import get_path

# logging
import logging
logger = logging.getLogger('forecaster.model.train')


class SmaTenHours(object):
    def __init__(self):
        self.trainer = Trainer()

    def load_model(self):
        path = get_path('model.h5')
        if not os.path.isfile(path):
            self.trainer.train()
        self.model = load_model(path)
        return self.model


class Trainer(object):
    def __init__(self):
        pass  # TODO

    def prepare_data(self, raw_data, grouped=False):
        data = np.array(raw_data)
        closes = data.transpose()[3]
        data = data[14:]
        sma_values = [sma(x, 14) for x in group(closes, 14)]
        rsi_values = [x/100 for x in rsi(closes, 14)]
        data = np.c_[data, np.expand_dims(sma_values, axis=1)]
        data = np.c_[data, np.expand_dims(rsi_values, axis=1)]
        if grouped is True:
            data = group(data, 10)
        else:
            data = [data]
        data = self.big_scale(data)
        return data

    def get_raw_data(self):
        """get raw data from website"""
        URL = ('http://api.fxhistoricaldata.com/indicators?instruments=EURUSD&expression' +
               '=open,high,low,close&item_count=50000&format=csv&timeframe=hour')
        raw_data = pd.read_csv(URL)  # get raw_data
        # change columns
        raw_data.columns = ['Currency', 'Datetime', 'open', 'high', 'low', 'close']
        raw_data = raw_data.iloc[::-1]  # reverse order
        Currencies = raw_data.Currency.unique()  # isolate currencies and drop useless columns
        dic = {elem: pd.DataFrame for elem in Currencies}
        for key in dic.keys():  # iterate for keys
            dic[key] = raw_data[:][raw_data.Currency == key].drop(
                ['Currency', 'Datetime'], axis=1)
        return dic

    def big_scale(self, arr):
        data = []
        for dataframe in arr:
            frame = np.array([x[:5] for x in dataframe])  # get op, mx, mn, cl values
            scaled = scale(frame)  # scale frame
            scaled_dataframe = []  # init full dataframe scaled
            for i, x in enumerate(dataframe):
                scaled_dataframe.append(np.concatenate([scaled[i], x[5:]]))  # append row combined
            data.append(scaled_dataframe)  # append scaled_dataframe to data
        return data

    # create labels
    def make_labels(self, arr):
        labels = []
        for i, scale in enumerate(arr):
            open_p = scale[-1][-1]  # get the open price
            try:
                close_p = arr[i + 1][-1][-1]  # get close price
            except IndexError:
                pass  # ignore last close
            if close_p - open_p >= 0:
                labels.append(1)
            elif close_p - open_p < 0:
                labels.append(0)
        return labels

    # split
    def split(self, l, part):
        return (np.array(l[:part]), np.array(l[part:]))

    def make_nn(self, hours):
        # neural network
        model = Sequential()
        model.add(LSTM(4, input_shape=(hours, 6)))
        model.add(Dense(20))
        model.add(Activation('relu'))
        model.add(Dense(1))
        model.add(Activation('sigmoid'))
        # For a mean squared error regression problem
        model.compile(optimizer='rmsprop',
                      loss='mse',
                      metrics=['accuracy'])
        self.model = model
        return model

    # prediction
    def predict(self, test, test_label):
        logger.debug("testing")
        predicted = self.model.predict(test)
        actual = test_label
        check_list = []
        for x in range(len(predicted)):
            if actual[x] >= 0.8 or actual[x] <= 0.2:
                if abs(predicted[x] - actual[x]) <= 0.2:
                    check_list.append(1)
                elif abs(predicted[x] - actual[x]) > 0.2:
                    check_list.append(-1)
            else:
                check_list.append(0)
        print('percentage - %f' % np.mean(check_list))

    # main func
    def train(self):
        logger.info("start training")
        raw_data = self.get_raw_data()['EURUSD']
        raw_data = raw_data.iloc[::-1]
        logger.debug("got raw data")
        labels = self.make_labels(group(raw_data.values[14:], 10))
        logger.debug("prepared labels")
        data = self.prepare_data(raw_data.values, True)
        logger.debug("prepared data")
        mod = self.make_nn(10)
        logger.debug("built neural network")
        x_train, x_test = self.split(data, -10000)
        y_train, y_test = self.split(labels, -10000)
        mod.fit(x_train, y_train, epochs=10, batch_size=64)
        logger.debug("fit")
        mod.evaluate(x_test, y_test)
        self.predict(x_test, y_test)
        path = get_path('model.h5')
        mod.save(path)
        logger.debug("saved model")
