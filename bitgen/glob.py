# -*- coding: utf-8 -*-

"""
bitgen.glob
~~~~~~~~~~~~~~

This module contains all strategies file paths.
"""

import os
import os.path
import yaml
from bitgen.patterns import Subject, Observer, Singleton

# logging
import logging
logger = logging.getLogger('bitgen.glob')


# define singleton collector of configurers
class Collector(Observer, metaclass=Singleton):
    """collect all data"""
    def __init__(self):
        self.collection = {}

    def mount(self, strat_nam):
        logger.debug("mounting %s" % strat_nam)
        path = getattr(FilePathes, strat_nam)
        conf = Configurer(path)
        conf.name = strat_nam
        conf.attach(self)
        conf.read()

    def notify(self, observable, event, name):
        if event == 'update' and isinstance(name, str):
            self.collection[name] = observable


# define yaml configuration file handler
class Configurer(Subject):
    """provides configuration data"""
    def __init__(self, path):
        super().__init__()
        self.config_file = path
        self.name = None
        self.config = {}

    def read(self):
        self.checkFile()
        with open(self.config_file, 'r') as f:
            yaml_dict = yaml.load(f)
            if yaml_dict is not None:
                self.config = yaml_dict
        self.notify_observers(event='update', name=self.name)
        return self.config

    def checkFile(self):
        if not os.path.isfile(self.config_file):
            directory = os.path.dirname(self.config_file)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(self.config_file, 'w') as f:
                pass

    def save(self):
        self.checkFile()
        if not self.config:
            logger.error("nothing to save (config not exists)")
            raise NotImplemented()
        with open(self.config_file, 'w') as f:
            f.write(yaml.dump(self.config))
        logger.debug("saved data")


def get_path(name):
    data_folder = os.path.join(os.path.dirname(__file__), 'data')
    file_path = os.path.join(data_folder, name)
    if not os.path.isfile(file_path):
        logger.debug("%s not found" % file_path)
    return file_path


# define namespace for file pathes
class FilePathes(object):
    """namespace"""
    SECURITY_DATA = get_path('security.yml')
    PERS_DATA = get_path('data.yml')
