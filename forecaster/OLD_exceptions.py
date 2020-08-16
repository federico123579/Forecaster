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


class MissingToken(Exception):
    def __init__(self):
        msg = "tokens not found in environment variables, please run setup.sh first."
        logger.error(msg)
        super().__init__(msg)
