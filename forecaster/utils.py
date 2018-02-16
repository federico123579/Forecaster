#!/usr/bin/env python

"""
forecaster.utils
~~~~~~~~~~~~~~

Contains all the utils of module, patterns and Abstract classes.
"""

import logging
import os.path

import yaml

logger = logging.getLogger('forecaster.utils')


def get_path(file_name):
    """get path of file in data folder (used mainly in strategy)"""
    data_folder = os.path.join(os.path.dirname(__file__), 'data')
    file_path = os.path.join(data_folder, file_name)
    if not os.path.isfile(file_path):
        logger.debug("%s not found in data folders" % file_path)
    return file_path


def read_yml(path):
    """read yaml and return dict"""
    with open(path, 'r') as yaml_file:
        yaml_dict = yaml.load(yaml_file)
        if yaml_dict is not None:
            config = yaml_dict
    return config
