#!/usr/bin/env python

"""
forecaster.predict.utils
~~~~~~~~~~~~~~

Various utils to predicter.
"""


def AverageTrueRange(candles):
    ATR = 0.0
    for candle in candles[1:]:
        ATR = (ATR * (len(candles) - 1) + (candle['high'] - candle['low'])) / len(candles)
    return ATR
