#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

from bitgen.view.main import View

# logging
import logging
logger = logging.getLogger('bitgen')


class Bot(object):
    def __init__(self):
        self.view = View()
