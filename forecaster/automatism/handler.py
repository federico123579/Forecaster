# -*- coding: utf-8 -*-

"""
forecaster.automatism.handler
~~~~~~~~~~~~~~

This is the module containing the inteface of API for automata.
"""

import time
from trading212api.exceptions import *

# logging
import logging
logger = logging.getLogger('forecaster.automatism.handler')


class Handler(object):
    """Interface for apis"""
    def __init__(self, controller):
        self.controller = controller
        self.client = controller.client.client

    def time_left_to_update(self):
        """get time left to update of hist data"""
        hist = self.controller.hist_data('EURUSD', 1)  # check EURUSD for convention
        last_time = int(str(hist[0]['timestamp'])[:-3])  # remove post comma superflous zeros
        time_left = (60-(time.time()-last_time)/60)*60
        logger.debug("time left (in minutes): %f" % (time_left/60))
        return time_left

    def transaction(self, mode, name, margin):
        """make auto-quantity transaction"""
        unit = self.client.get_margin(name, 10)/10
        quantity = int(margin / unit)  # get quantity
        while True:
            try:
                margin = self.client.get_margin(name, quantity)
                self.client.open_position(mode, name, quantity)
                break
            except (MinQuantityExceeded, MaxQuantityExceeded) as e:
                logger.warning("minimum or maximum quantity reached")
                quantity = e.limit
            except ProductNotAvaible as e:
                raise
            except PriceChangedException as e:
                continue
            except Exception as e:
                logger.error("transaction failed")
                logger.exception(e)
        return {'margin': margin, 'quantity': quantity}
