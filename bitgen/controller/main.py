# -*- coding: utf-8 -*-

"""
bitgen.controller.main
~~~~~~~~~~~~~~

This module provides the main controller component of the model MVC.
"""

from bitgen.patterns import Subject, Observer
from bitgen.controller.coinbase import CoinbaseAPI
from bitgen.controller.exceptions import *
from bitgen.view import View

# logging
import logging
logger = logging.getLogger('bitgen.controller')


# define a superior controller
class UltraController(Observer):
    """control views and models"""
    def __init__(self):
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
            self.controller.start_bot()
        elif event == 'stop-bot':
            self.controller.stop_bot()
        elif event == 'config':
            self.view.configurate()


# define a general controller
class Controller(Subject, Observer):
    """control all controllers"""
    def __init__(self):
        super().__init__()
        self.coinbase = CoinbaseAPI(self)

    def start_bot(self):
        try:  # connect to coinbase
            self.coinbase.start()
        except MissingConfig:
            self.notify_observers('config')
        # TODO start bot function

    def stop_bot(self):
        pass
        # TODO stop bot function
