
# -*- coding: utf-8 -*-

"""
forecaster.controller.tradingapi
~~~~~~~~~~~~~~

This module provides the the controller for API.
"""

from trading212api import Client
from forecaster.controller.glob import OmniController, DefaultController

# logging
import logging
logger = logging.getLogger('forecaster.controller.tradingapi')


class ClientController(DefaultController):
    """controller handler of trading212 api"""
    def __init__(self, mode):
        super().__init__()
        self.client = Client(mode)

    def start(self):
        username = OmniController().pers_data['username']
        password = OmniController().pers_data['password']
        self.client.login(username, password)
        logger.debug("Logged in as %s" % username)
