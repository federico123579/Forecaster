# -*- coding: utf-8 -*-

"""
forecaster.exceptions
~~~~~~~~~~~~~~

This module provides main exceptions.
"""

# logging
import logging
logger = logging.getLogger('forecaster.exceptions')


class MissingConfig(Exception):
    def __init__(self):
        msg = "configuration not found"
        logger.error(msg)
        super().__init__(msg)