#!/usr/bin/env python

"""
forecaster.utils
~~~~~~~~~~~~~~

Contains all the utils of module, patterns and Abstract classes.
"""
import abc
import logging
import os.path
from enum import Enum, auto

import yaml

logger = logging.getLogger('forecaster.utils')


class STATES(Enum):
    POWERED_OFF = auto()
    MISSING_DATA = auto()
    READY = auto()
    POWERED_ON = auto()
    STOPPED = auto()


class EVENTS(Enum):
    START_BOT = auto()
    STOP_BOT = auto()
    MISSING_DATA = auto()
    CLOSED_POS = auto()


class ACTIONS(Enum):
    BUY = auto()
    SELL = auto()


TIMEFRAME = {
    '1d': 60 * 60 * 24,
    '4h': 60 * 60 * 4,
    '1h': 60 * 60,
    '15m': 60 * 15,
    '10m': 60 * 10,
    '5m': 60 * 5,
    '1m': 60
}


def read_strategy(name):
    return read_yml(get_yaml(name))


def get_yaml(name):
    return get_path(name + '.yml')


def read_yml(path):
    """read yaml and return dict"""
    with open(path, 'r') as yaml_file:
        yaml_dict = yaml.load(yaml_file)
        if yaml_dict is not None:
            config = yaml_dict
    return config


def save_yaml(data, path):
    """save dict to yaml"""
    with open(path, 'w') as yaml_file:
        yaml_file.write(yaml.dump(data))


def get_path(file_name):
    """get path of file in data folder (used mainly in strategy)"""
    data_folder = os.path.join(os.path.dirname(__file__), 'data')
    file_path = os.path.join(data_folder, file_name)
    return file_path


# ~~{ DESIGN PATTERNS }~~
class Singleton(type):
    """
    Define an Instance operation that lets clients access its unique
    instance.
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class Chainer(metaclass=abc.ABCMeta):
    """
    Define an interface for handling requests.
    Implement the successor link.
    """

    def __init__(self, successor=None):
        self._successor = successor

    def pass_request(self, request, **kwargs):
        logger.debug("caught request: %s" % request)
        if self._successor is not None:
            self._successor.handle_request(request)

    @abc.abstractmethod
    def handle_request(self):
        pass


class Stater(object):
    """
    Define an interface to assing states
    """

    def __init__(self):
        self.state = STATES.POWERED_OFF

    def set_state(self, state):
        """log state"""
        self.state = STATES[state]
        logger.debug("%s state: %s" % (self.__class__.__name__, STATES[state].name))


class StaterChainer(Stater, Chainer):
    def __init__(self, successor=None):
        Stater.__init__(self)
        Chainer.__init__(self, successor)
