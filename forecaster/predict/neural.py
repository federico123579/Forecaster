#!/usr/bin/env python

"""
forecaster.predict.neural
~~~~~~~~~~~~~~

Contains all NN utils and model.
Use a strategy pattern to work with a yml file.
"""

import logging

import pandas as pd
from keras.layers import LSTM, Activation, Dense, Dropout
from keras.models import Sequential, load_model
from keras.optimizers import Adam

from forecaster.predict.tools import *
from forecaster.utils import get_path, read_yml

logger = logging.getLogger('forecaster.predict.neural')


class NeuralNetwork(object):
    """feed with strategy"""

    def __init__(self, strategy_name):
        strategy_path = get_path(strategy_name + '.yml')
        self.strategy = read_yml(strategy_path)
        self.FUNC_CONV = {
            'default': self._default_values,
            'sma': self._sma_values,
            'rsi': self._rsi_values,
            'stochastic_oscillator': self._stochastic_values}
        logger.debug("NeuralNetwork initied with %s" % strategy_name)

    def train(self):
        data, labels = self.get_data()
        self.make_nn([data.shape[1], data.shape[2]])
        limit = int(-self.strategy['item_count'] * self.strategy['train_test'])
        x_train, x_test = self._split(data, limit)
        y_train, y_test = self._split(labels, limit)
        logger.debug("splitted")
        epochs = self.strategy['epochs']
        batch_size = self.strategy['batch_size']
        self.model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size)
        logger.debug("trained model")
        eff1 = self.model.evaluate(x_test, y_test)[0]
        eff2 = self.predict(x_test, y_test)
        logger.debug("Efficency 1: %f" % eff1)
        logger.debug("Efficency 2: %f" % eff2)

    def predict(self, test, test_label):
        """test model"""
        logger.debug("testing")
        predicted = self.model.predict(test)
        actual = test_label
        check_list = 0
        for x in range(len(predicted)):
            risk_range = 0.5
            if abs(predicted[x] - actual[x]) <= risk_range:
                check_list += 1
            elif abs(predicted[x] - actual[x]) > risk_range:
                check_list += 0
        return check_list/len(predicted)

    def make_nn(self, shape):
        """make neural network"""
        model = Sequential()
        # model.add(LSTM(7, input_shape=(shape[0], shape[1])))
        model.add(LSTM(64, input_shape=(shape[0], shape[1])))
        model.add(Dropout(0.5))
        model.add(Dense(16, activation='relu'))
        model.add(Dense(1, activation='sigmoid'))
        # model.add(Dense(70, activation='relu'))
        # For a mean squared error regression problem
        model.compile(optimizer=Adam(lr=self.strategy['learning_rate']),
                      loss='mse',
                      metrics=['accuracy'])
        self.model = model
        logger.debug("built neural network")
        return model

    def get_data(self):
        """prepare data"""
        data = self._get_raw_data_from_url(['open', 'high', 'low', 'close'])
        logger.debug("got data from url")
        labels = self.make_labels(data)
        logger.debug("made labels")
        # start decorator loop
        for parameter in self.strategy['parameters']:
            func = self.FUNC_CONV[parameter['name']]
            if 'options' in parameter.keys():
                data = func(data, **parameter['options'])
            else:
                data = func(data)
            logger.debug("%s executed" % parameter['name'])
        # clear
        data = self._clear_nan(data)
        logger.debug("cleared NaN")
        # scale
        data = self._group(data)
        logger.debug("grouped data")
        if self.strategy['scale']:
            data = self._scale(data)
            logger.debug("scaled data")
        # normalize
        labels = labels[len(labels) - len(data):]
        logger.debug("normalized")
        return data, labels

    def make_labels(self, dataframe):
        """make labels"""
        labels = []
        for first, last in zip(dataframe.close, dataframe.close[1:]):
            diff = last - first
            if diff > 0:
                labels.append(1)
            else:
                labels.append(0)
        return np.array(labels)

    @staticmethod
    def _split(array, index):
        return np.array(array[:index]), np.array(array[index:])

    def _scale(self, array):
        """decorator function"""
        scaled = []
        for group in array:
            columns = []
            for col in group.T:  # iterate over columns
                vals = col.reshape(-1, 1)
                columns.append(scale(vals))  # scale
            scaled.append(np.concatenate(columns, axis=1))
        return np.array(scaled)

    def _group(self, dataframe):
        """decorator function"""
        periods = self.strategy['window_size']
        grouped = []
        for x in range(len(dataframe) - periods):  # iter in DataFrame
            frame = dataframe[x:x + periods]  # get window
            grouped.append(frame.values)
        return np.array(grouped)

    def _clear_nan(self, dataframe):
        """decorator function"""
        for index, row in dataframe.iterrows():
            if any([x for x in row if np.isnan(x)]):
                dataframe = dataframe.drop(index, axis=0)
        return dataframe

    def _stochastic_values(self, dataframe):
        """decorator function"""
        stochastics = dataframe.close.rolling(12).apply(stochastic)
        return dataframe.assign(stochastic=stochastics)

    def _rsi_values(self, dataframe, periods):
        """decorator function"""
        rsis = dataframe.close.rolling(periods).apply(rsi, args=(periods,))
        return dataframe.assign(rsi=rsis)

    def _sma_values(self, dataframe, periods):
        """decorator function"""
        smas = dataframe.close.rolling(periods).apply(sma, args=(periods,))
        return dataframe.assign(sma=smas)

    def _default_values(self, dataframe, pars):
        """decorator function"""
        pars_to_delete = [par for par in ['open', 'high', 'low', 'close'] if par not in pars]
        return dataframe.drop(pars_to_delete, axis=1)

    def _get_raw_data_from_url(self, pars):
        """get data from url"""
        URL = ('http://api.fxhistoricaldata.com/indicators' +
               '?instruments=EURUSD' +
               '&expression=%s' +
               '&item_count=%s' +
               '&format=csv&timeframe=%s')
        expression = ','.join(pars)
        url = URL % (expression, self.strategy['item_count'], self.strategy['timeframe'])
        raw_data = pd.read_csv(url)  # read csv from url
        columns = ['Currency', 'Datetime']
        columns.extend(pars)
        raw_data.columns = columns
        raw_data = raw_data.drop(['Currency', 'Datetime'], axis=1)  # drop useless columns
        return raw_data.iloc[::-1]  # return data reversed
