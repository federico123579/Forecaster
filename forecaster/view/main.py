# -*- coding: utf-8 -*-

"""
forecaster.view.main
~~~~~~~~~~~~~~

This module provides the main view component of the model MVC.
"""

from forecaster.patterns import Subject, Observer
from forecaster.view.tele import TeleViewer

# logging
import logging
logger = logging.getLogger('forecaster.view')


# define a general view client
class View(Subject, Observer):
    """main view component"""
    def __init__(self):
        super().__init__()
        self.tele = TeleViewer(self)

    def start(self):
        self.tele.listen()

    def configurate(self):
        self.tele.config_needed()

    def prediction(self, pred_dict):
        self.tele.out_pred(pred_dict)

    # handle all events
    def notify(self, observable, event):
        logger.debug("View notified - %s" % event)
        self.notify_observers(event)
