# -*- coding: utf-8 -*-

"""
forecaster.controller.main
~~~~~~~~~~~~~~

This module provides the main controller component of the model MVC.
"""

from forecaster.patterns import Subject, Observer
from forecaster.controller.tradingapi import ClientController
from forecaster.model import Model
from forecaster.view import View
from forecaster.controller.exceptions import *

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

    # handle all events
    def notify(self, observable, event):
        logger.debug("Controller notified - %s" % event)
        if event == 'start-bot':
            self.model.start()
            self.controller.start_bot()
        elif event == 'stop-bot':
            self.controller.stop_bot()
        elif event == 'config':
            self.view.configurate()
        elif event == 'predict':
            try:
                self.view.prediction(self.model.pred_all())
            except Exception as e:
                logger.exception(e)


# define a general controller
class Controller(Subject, Observer):
    """control all controllers"""
    def __init__(self):
        super().__init__()
        self.client = ClientController('demo')

    def start_bot(self):
        self.client.start()
        logger.debug("Controller started")

    def stop_bot(self):
        pass
        # TODO stop bot function
