#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
forecaster.core.model.train
~~~~~~~~~~~~~~

This module provide training of the Neural Network.
"""

import os.path
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, Activation, LSTM
from forecaster.glob import get_path

# logging
import logging
logger = logging.getLogger('forecaster.model.train')


# get raw data from website
def get_raw_data():
    raw_data = pd.read_csv('http://api.fxhistoricaldata.com/indicators?instruments=EURUSD' +
                           '&expression=open,high,low,close&item_count=50000&format=' +
                           'csv&timeframe=hour')
    # change columns
    raw_data.columns = ['Currency', 'Datetime', 'open', 'high', 'low', 'close']
    # reverse order
    raw_data = raw_data.iloc[::-1]
    # isolate currencies and drop useless columns
    Currencies = raw_data.Currency.unique()
    dic = {elem: pd.DataFrame for elem in Currencies}
    # iterate for keys
    for key in dic.keys():
        dic[key] = raw_data[:][raw_data.Currency == key].drop(
            ['Currency', 'Datetime'], axis=1)
    return dic


# group by hours
def group_by(arr, n):
    # group by hours
    data = []
    for i in range(len(arr)-n):
        data.append(arr[i:i+n])
    return np.array(data)


# simple moving average
def sma(values, periods):
    return sum(values)/periods


# scale
def scale(arr):
    # scale
    data = []
    for dataframe in arr:
        scaler = MinMaxScaler(feature_range=(-1, 1))
        scaler.fit(dataframe)
        data.append(np.array(scaler.transform(dataframe)))
    return data


# create labels
def make_labels(arr):
    labels = []
    for i, scale in enumerate(arr):
        open_p = scale[-1][-1]  # get the open price
        try:
            close_p = arr[i+1][-1][-1]  # get close price
        except IndexError:
            pass  # ignore last close
        if close_p - open_p >= 0:
            labels.append(1)
        elif close_p - open_p < 0:
            labels.append(0)
    return labels


# split
def split(l, part):
    return (np.array(l[:part]), np.array(l[part:]))


def make_nn(hours):
    # neural network
    model = Sequential()
    model.add(LSTM(4, input_shape=(hours, 5)))
    model.add(Dense(20))
    model.add(Activation('relu'))
    model.add(Dense(1))
    model.add(Activation('sigmoid'))
    # For a mean squared error regression problem
    model.compile(optimizer='rmsprop',
                  loss='mse',
                  metrics=['accuracy'])
    return model


# prediction
def predict(test, test_label, predicted):
    predicted = model.predict(x_test)
    actual = y_test
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
    print('ones - %d' % len([x for x in check_list if x == 1]))


# main func
def train(epochs=10):
    logger.info("start training")
    raw_data = get_raw_data()['EURUSD']
    raw_data = raw_data.iloc[::-1]
    logger.debug("got raw data")
    closes = raw_data.values.transpose()[3]
    sma_values = [sma(x, 14) for x in group_by(closes, 14)]
    logger.debug("got smas")
    data = np.c_[raw_data.values[14:], np.expand_dims(sma_values, axis=1)]
    data = group_by(data, 10)
    logger.debug("grouped")
    labels = make_labels(data)
    logger.debug("labels")
    data = scale(data)
    logger.debug("scaled")
    mod = make_nn(10)
    logger.debug("made neural network")
    x_train, x_test = split(data, -1)
    y_train, y_test = split(labels, -1)
    mod.fit(x_train, y_train, epochs=epochs, batch_size=64)
    logger.debug("fit")
    path = get_path('model.h5')
    mod.save(path)
    logger.debug("saved model")


if __name__ == "__main__":
    train(10)
