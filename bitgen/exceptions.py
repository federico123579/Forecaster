# -*- coding: utf-8 -*-

"""
bitgen.exceptions
~~~~~~~~~~~~~~

This module provides main exceptions.
"""

# logging
import logging
logger = logging.getLogger('bitgen.exceptions')


class MissingConfig(Exception):
    def __init__(self):
        msg = "configuration not found"
        logger.error(msg)
        super().__init__(msg)