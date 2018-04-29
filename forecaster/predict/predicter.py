"""
forecaster.predict.predicter
~~~~~~~~~~~~~~

Facade class to predict working with algorithms.
"""

import logging

from forecaster.enums import ACTIONS
from forecaster.handler import Client
from forecaster.predict import utils, algorithms as algos
from forecaster.security import Preserver

LOGGER = logging.getLogger('forecaster.predict')


class Predicter(object):
    """Adapter proxy class to interface with predictive algorithms"""

    def __init__(self, strategy):
        self.strategy = strategy
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
        algo = FactoryPredicter[algo_name](algo_name)
        setattr(self, algo.__class__.__name__.replace('Predicter', ''), algo)
        self.algos.add(algo)
        LOGGER.debug("{} algorithm initied".format(algo_name))

    def predict(self, symbol, interval, timeframe):
        """get prediction based on weight, get_predictions"""
        prediction_score = 0.0  # score of modes
        positive_score = 0.0  # score of ranking bullish
        negative_score = 0.0  # score of ranking bearish
        predictions = self.get_predictions(symbol, interval, timeframe)
        for algo in self.algos:  # check for every algorithm
            prediction = predictions[algo.name]
            algo_score = algo.get_weight()  # weight of algorithm
            scores_register = algo.scores[str((interval, timeframe))]
            prediction_score = scores_register[symbol]
            # get reverse rank of score among others from 1 to 5
            rank = list(reversed(sorted(scores_register.items(), key=lambda x: x[1])))
            score_rank = rank.index((symbol, prediction_score)) + 1
            if score_rank > self.preserver.concurrent_movements:
                return utils.Prediction(ACTIONS.DISCARD)
            # transform index in score on percent
            score = score_rank / self.preserver.concurrent_movements
            # if bullish add point to total score and positive_score based on score of prediction
            if prediction.action == ACTIONS.BUY:
                prediction_score += algo_score
                positive_score += score * algo_score
            # if bearish substract point to total score and negative_score
            elif prediction.action == ACTIONS.SELL:
                prediction_score -= algo_score
                negative_score += score * algo_score
        weights_sum = sum([x.get_weight() for x in self.algos])
        relative_strenght = abs(prediction_score) / weights_sum
        if relative_strenght >= self.preserver.relative_threshold:
            if prediction_score > 0:
                # final score is mean of score trough algos and multiplied
                # for the strenght of decision
                final_score = positive_score / weights_sum * relative_strenght
                return utils.Prediction(ACTIONS.BUY, final_score)
            elif prediction_score < 0:
                final_score = negative_score / weights_sum * relative_strenght
                return utils.Prediction(ACTIONS.SELL, final_score)
        return utils.Prediction(ACTIONS.DISCARD)

    def get_predictions(self, symbol, interval, timeframe):
        candles = self.client.get_last_candles(symbol, interval, timeframe)
        predictions = {}
        for algo in self.algos:  # check for every algorithm
            prediction = algo.predict(candles)
            predictions[algo.name] = prediction
            if not isinstance(algo.scores.get(str((interval, timeframe))), dict):
                algo.scores[str((interval, timeframe))] = {}
            scores_register = algo.scores.get(str((interval, timeframe)))
            scores_register[symbol] = prediction.score
        return predictions


# factory class
FactoryPredicter = {
    'mean_rev': algos.MeanReversionPredicter,
    'three_stars': algos.ThreeStarsInTheSouthPredicter
}
