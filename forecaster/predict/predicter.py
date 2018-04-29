"""
forecaster.predict.predicter
~~~~~~~~~~~~~~

Facade class to predict working with algorithms.
"""

import logging

import forecaster.predict.algorithms as algos
import forecaster.predict.utils as utils
from forecaster.enums import ACTIONS
from forecaster.handler import Client
from forecaster.security import Preserver
from forecaster.utils import read_strategy

LOGGER = logging.getLogger('forecaster.predict')


class Predicter(object):
    """Adapter proxy class to interface with predictive algorithms"""

    def __init__(self, bot):
        super().__init__(bot)
        self.strategy = read_strategy('predicter')
        self.client = Client()
        self.preserver = Preserver()
        self.algos = set()
        self._init_algos()  # init all algos
        LOGGER.debug("Predicter initied")

    def _init_algos(self):
        """initiate algorithms"""
        for algo_name in self.strategy['algos']:
            self._init_algo(algo_name)

    def _init_algo(self, algo_name):
        """initiate an algorithm"""
        try:  # if strategy exists
            algo = FactoryPredicter[algo_name](algo_name)
        except FileNotFoundError:
            algo = FactoryPredicter[algo_name]
        setattr(self, algo.__class__.__name__.replace('Predicter', ''), algo)
        self.algos.add(algo)
        LOGGER.debug("{} algorithm initied".format(algo_name))

    def predict(self, symbol, interval, timeframe):
        """get prediction based on weight"""
        candles = self.client.get_last_candles(symbol, interval, timeframe)
        prediction_score = 0.0  # score of modes
        positive_score = 0.0  # score of ranking bullish
        negative_score = 0.0  # score of ranking bearish
        for algo in self.algos:  # check for every algorithm
            prediction = algo.predict(candles)
            score = algo.get_weight()  # weight of algorithm
            # if bullish add point to total score and positive_score based on score of prediction
            if prediction.action == ACTIONS.BUY:  # FROM HERE
        weights_sum = sum([x.strategy['weight'] for x in self.algos])
        relative_strenght = abs(prediction_score) / weights_sum
        if relative_strenght > limit:
            if prediction_score > 0:
                return utils.Prediction(ACTIONS.BUY, positive_score * relative_strenght)
            elif prediction_score < 0:
                return utils.Prediction(ACTIONS.SELL, negative_score * relative_strenght)
        return utils.Prediction(ACTIONS.DISCARD)

    def get_score(self, symbol, interval, timeframe):
        candles = self.client.get_last_candles(symbol, interval, timeframe)
        prediction = self.predict(symbol, interval, timeframe)
        total_score = 0
        for algo in self.algos:
            score = algo.get_score(candles)
            # TODO
        return total_score


# factory class
FactoryPredicter = {
    'mean_rev': algos.MeanReversionPredicter,
    'three_stars': algos.ThreeStarsInTheSouthPredicter
}
