#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

from forecaster.controller import UltraController

# logging
import logging
logger = logging.getLogger('forecaster')


class Bot(UltraController):
    def __init__(self):
        super().__init__()
