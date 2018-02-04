# -*- coding: utf-8 -*-

"""
forecaster.automatism.handler
~~~~~~~~~~~~~~

This module contains the handler.
"""

import time

# logging
import logging
logger = logging.getLogger('forecaster.controller.glob')


class Handler(object):
    """Interface for apis"""
    def __init__(self, controller):
        self.controller = controller
        self.client = controller.client

    def time_left_to_update(self):
        """get time left to update of hist data"""
        hist = self.controller.hist_data('EURUSD', 1)  # check EURUSD for convention
        last_time = int(str(hist['timestamp'])[:-3])  # remove post comma superflous zeros
        time_left = (60-(time.time()-last_time)/60)*60
        return time_left
