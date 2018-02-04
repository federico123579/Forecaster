
# -*- coding: utf-8 -*-

"""
forecaster.controller.tradingapi
~~~~~~~~~~~~~~

This module provides the the controller for API.
"""

from trading212api import Client
from forecaster.controller.glob import OmniController, DefaultController
from forecaster.exceptions import MissingConfig

# logging
import logging
logger = logging.getLogger('forecaster.controller.tradingapi')


class ClientController(DefaultController):
    """controller handler of trading212 api"""
    def __init__(self, mode):
        super().__init__(self)
        self.client = Client(mode)

    def start(self):
        try:
            username = OmniController().pers_data['username']
            password = OmniController().pers_data['password']
        except KeyError:
            raise MissingConfig
        self.client.login(username, password)
        logger.debug("Logged in as %s" % username)
