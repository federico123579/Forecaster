#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

from cryptotrader.view.main import View

# logging
import logging
logger = logging.getLogger('cryptotrader')


class Bot(object):
    def __init__(self):
        self.view = View()
