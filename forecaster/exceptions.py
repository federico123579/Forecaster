# -*- coding: utf-8 -*-

"""
forecaster.exceptions
~~~~~~~~~~~~~~

This module provides exceptions.
"""

import logging

logger = logging.getLogger('forecaster.exceptions')


class MissingData(Exception):
    def __init__(self):
        msg = "configuration data not found"
        logger.error(msg)
        super().__init__(msg)


class MissingToken(Exception):
    def __init__(self):
        msg = "tokens not found in environment variables, please run setup.sh first."
        logger.error(msg)
        super().__init__(msg)


class ProductNotAvaible(Exception):
    def __init__(self):
        msg = "product not avaible"
        logger.error(msg)
        super().__init__(msg)


class QuantityError(Exception):
    def __init__(self, mode, quant):
        self.mode = mode
        self.quant = quant
        msg = "quantity error"
        logger.error(msg)
        super().__init__(msg)


class TransactionDiscarded(Exception):
    def __init__(self, prediction):
        self.prediction = prediction
        msg = "transaction discarded with prediction score of {}".format(prediction.score)
        super().__init__(msg)
