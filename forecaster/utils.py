"""
forecaster.utils
~~~~~~~~~~~~~~

Contains all the utils of module, patterns and Abstract classes.
"""

import configparser
import json
import os
import os.path

import termcolor
import yaml
from forecaster.exceptions import MissingToken


# +----------------------------------------------------------------------+
# | UTILITY FUNCTIONS                                                    |
# +----------------------------------------------------------------------+
# read strategy files from data folder
def read_strategy(name, folders=[]):
    return read_yml(get_yaml(name, folders))


# read strategy files from data folder
def read_data(name, folders=[]):
    return read_json(get_json(name, folders))


# read tokens in tokens.yml
def read_tokens():
    try:
        return get_conf()['TOKENS']
    except FileNotFoundError:
        raise MissingToken()


# get yaml path
def get_yaml(name, folders=[]):
    return get_path(name + '.yml', *folders)


# get json path
def get_json(name, folders=[]):
    return get_path(name + '.json', *folders)


# read yaml file
def read_yml(path):
    """read yaml and return dict"""
    with open(path, 'r') as yaml_file:
        return yaml.load(yaml_file)


# read json file
def read_json(path):
    """read yaml and return dict"""
    with open(path, 'r') as json_file:
        return json.load(json_file)


# save json file
def save_json(data, path):
    """save dict to yaml"""
    make_dirs(path)
    with open(path, 'w') as json_file:
        json.dump(data, json_file)


# make dirs if not exist
def make_dirs(path):
    folders, _ = os.path.split(path)
    if folders and not os.path.isdir(folders):
        os.makedirs(folders)


# get configuration
def get_conf():
    config = configparser.ConfigParser()
    path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config.read(path)
    return config


# save configuration
def save_conf(config):
    path = os.path.join(os.path.dirname(__file__), 'config.ini')
    with open(path, 'w') as configfile:
        config.write(configfile)


# get file in data folder
def get_path(*path):
    """get path of file in data folder (used mainly in strategy)"""
    data_folder = os.path.join(os.path.dirname(__file__), 'data')
    file_path = os.path.join(data_folder, *path)
    return file_path


# +----------------------------------------------------------------------+
# | COMMAND LINE INTERFACE FUCNTIONS                                     |
# +----------------------------------------------------------------------+
class CLI(object):
    """namespace"""
    @staticmethod
    def print_bold(text, *args, **kw):
        """print bold"""
        termcolor.cprint(text, attrs=['bold'], *args, **kw)

    @staticmethod
    def print_color(text, color):
        """print color"""
        termcolor.cprint(text, color)

    @staticmethod
    def colored(text, color):
        """return colored"""
        return termcolor.colored(text, color)
