#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
...model.predicters.sma_ten_hours
~~~~~~~~~~~~~~

Neural network that predict trend using 10 hours values and sma.
"""


class SmaTenHours(object):
    def __init__(self):
        pass


class Trainer(object):
    def get_raw_data(self):
        """get raw data from website"""
        URL = ('http://api.fxhistoricaldata.com/indicators?instruments=EURUSD&expression=open,high,' +
               'low,close&item_count=50000&format=csv&timeframe=hour')
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

    def big_scale(arr):
        data = []
        for dataframe in arr:
            data.append(scale(dataframe))
        return data

    # create labels
    def make_labels(arr):
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
        logger.debug("testing")
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

    # main func
    def train():
        logger.info("start training")
        raw_data = get_raw_data(URL)['EURUSD']
        raw_data = raw_data.iloc[::-1]
        logger.debug("got raw data")
        closes = raw_data.values.transpose()[3]
        sma_values = [sma(x, 14) for x in group(closes, 14)]
        logger.debug("got smas")
        data = np.c_[raw_data.values[14:], np.expand_dims(sma_values, axis=1)]
        data = group(data, 10)
        logger.debug("grouped")
        labels = make_labels(data)
        logger.debug("labels")
        data = big_scale(data)
        logger.debug("scaled")
        mod = make_nn(10)
        logger.debug("made neural network")
        x_train, x_test = split(data, -1)
        y_train, y_test = split(labels, -1)
        mod.fit(x_train, y_train, epochs=10, batch_size=64)
        logger.debug("fit")
        predict(x_test, y_test, mod.predict(x_test))
        path = get_path('model.h5')
        mod.save(path)
        logger.debug("saved model")
