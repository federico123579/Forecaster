# -*- coding: utf-8 -*-

"""
bitgen.model.exceptions
~~~~~~~~~~~~~~

This module provides exceptions for model.
"""

# logging
import logging
logger = logging.getLogger('bitgen.model.exceptions')


class MissingModel(Exception):
    def __init__(self):
        msg = "model not found"
        logger.error(msg)
        super().__init__(msg)
