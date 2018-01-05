# -*- coding: utf-8 -*-

"""
bitgen.controller.exceptions
~~~~~~~~~~~~~~

This module provides exceptions for controller.
"""

# logging
import logging
logger = logging.getLogger('bitgen.controller.exceptions')


class ActionNotPermitted(Exception):
    def __init__(self, action):
        super().__init__("%s action is not permitted by payment method" % action)
