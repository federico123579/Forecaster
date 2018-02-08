import numpy as np
from forecaster.core.controller import UltraController
from forecaster.core.model.utils import *
import logging

logger = logging.getLogger('forecaster.test.test_algo')


def main():
    logging.getLogger('forecaster').setLevel(logging.DEBUG)  # set logger
    bot = UltraController()  # init controller
    logger.debug("inited bot")
    client = bot.controller.client.client  # get client
    logger.debug("inited client")
    bot.model.forex.init_model()  # get model
    model = bot.model.forex.models['TenHours']
    model.load_model()
    logger.debug("got init model")
    trainer = model.trainer  # get trainer
    logger.debug("inited trainer")
    model = model.model
    client.login('davidjalter@dayrep.com', "***REMOVED***")
    logger.debug("logged in")
    raw_data = client.get_historical_data('USDJPY', 10000, '1m')
    logger.debug("got raw data")
    bid_data = [i['bid'] for i in raw_data]
    data = [[x['open'], x['high'], x['low'], x['close']] for x in bid_data]
    data.reverse()
    logger.debug("fix data")
    labels = trainer.make_labels(group(data, 10))
    logger.debug("made labels")
    data = trainer.prepare_data(data)
    logger.debug("prepared data")
    predicted = [model.predict(np.array([x])) for x in group(data[0], 10)]
    logger.debug("predicted")
    labels = labels[14:]
    diff = 0.5
    res = 0
    for i in range(len(predicted)):
        if predicted[i] > labels[i]-diff and labels[i] == 1:
            res += 1
        elif predicted[i] < labels[i]+diff and labels[i] == 0:
            res += 1
        else:
            res += 0
    print(res/len(predicted))


if __name__ == "__main__":
    main()
