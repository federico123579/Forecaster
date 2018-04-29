"""
forecaster.enums
~~~~~~~~~~~~~~

Contains all Enums and dicts used in package.
"""

from enum import Enum, auto


class EVENTS(Enum):
    # EXCEPTIONS
    MISSING_DATA = auto()
    MODE_FAILURE = auto()
    # TELEGRAM NOTIFICATIONS
    OPENED_POS = auto()
    CLOSED_POS = auto()
    CLOSED_ALL_POS = auto()
    MARKET_CLOSED = auto()
    PRODUCT_NOT_AVAIBLE = auto()
    CONNECTION_ERROR = auto()


class ACTIONS(Enum):
    # MAIN BOT
    START_BOT = auto()
    STOP_BOT = auto()
    SHUTDOWN = auto()
    # CLIENT
    CHANGE_MODE = auto()
    # PRESERVER
    GET_USABLE_MARGIN = auto()
    # PREDICTER
    PREDICT = auto()
    # PREDICTION ACTIONS
    BUY = 'buy'
    SELL = 'sell'
    DISCARD = auto()


class STATUS(Enum):
    READY = auto()
    ON = auto()
    OFF = auto()


TIMEFRAME = {
    '1d': 60 * 60 * 24,
    '4h': 60 * 60 * 4,
    '1h': 60 * 60,
    '15m': 60 * 15,
    '10m': 60 * 10,
    '5m': 60 * 5,
    '1m': 60
}


DIRECTIONS = {
    'sell': 'ask',
    'buy': 'bid'
}
