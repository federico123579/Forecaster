# -*- coding: utf-8 -*-

"""
forecaster.core.controller.main
~~~~~~~~~~~~~~

This module provides the main controller component of the model MVC.
"""

from forecaster.patterns import Subject, Observer
from forecaster.core.controller.tradingapi import ClientController
from forecaster.core.model import Model
from forecaster.core.view import View

# logging
import logging
logger = logging.getLogger('forecaster.controller')


# define a superior controller
class UltraController(Observer):
    """control views and models"""
    def __init__(self):
        self.model = Model()  # init model
        self.register_obs(self.model)
        self.controller = Controller()  # init controller
        self.register_obs(self.controller)
        self.view = View()  # init view
        self.register_obs(self.view)

    def start(self):
        self.view.start()  # listen commands

    def stop(self):
        self.view.stop()  # stop the updater

    # handle all events
    def notify(self, observable, event, **kwargs):
        logger.debug("Controller notified - %s" % event)
        if event == 'start-bot':
            self.model.start()
            self.controller.start_bot()
        elif event == 'stop-bot':
            self.controller.stop_bot()
        elif event == 'config':
            self.view.configurate()
        elif event == 'historical_data':  # get hist candles with amount
            self.model.forex.hist = self.controller.hist_data(  # OPTIMIZE
                kwargs['data']['name'], kwargs['data']['limit'])
        elif event == 'predict':
            self.view.prediction(self.model.pred_all())


# define a general controller
class Controller(Subject, Observer):
    """control all controllers"""
    def __init__(self):
        super().__init__()
        self.client = ClientController('demo')

    def start_bot(self):
        try:  # try to log in
            self.client.start()
        except MissingConfig:  # if credentials not in config
            self.notify_observers('config')
        logger.debug("Controller started")

    def stop_bot(self):
        pass
        # TODO stop bot function

    def hist_data(self, name, amount):
        """get historical data"""
        return self.client.client.get_historical_data(name, amount, '1h')
