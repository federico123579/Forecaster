# -*- coding: utf-8 -*-

"""
forecaster.exceptions
~~~~~~~~~~~~~~

This module provides exceptions.
"""

import logging

logger = logging.getLogger('forecaster.exceptions')


class MissingData(Exception):
    def __init__(self):
        msg = "configuration data not found"
        logger.error(msg)
        super().__init__(msg)
