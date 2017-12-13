# -*- coding: utf-8 -*-

"""
cryptotrader.view.main
~~~~~~~~~~~~~~

This module provides the main view component of the model MVC.
"""

from cryptotrader.patterns import Observer
from cryptotrader.view.tele import TeleViewer

# logging
import logging
logger = logging.getLogger('cryptotrader.view')


# define a general view client
class View(Observer):
    """main view component"""
    def __init__(self):
        self.tele = TeleViewer(self)

    # handle all events
    def notify(self, observable, event):
        logger.debug("View notified - %s" % event)
        table = {
            'start-bot': None,
            'stop-bot': None
        }
        return table.get(event)
