"""
forecaster.utils
~~~~~~~~~~~~~~

Contains all the utils of module, patterns and Abstract classes.
"""

import os.path

import yaml

from forecaster.exceptions import MissingToken


# +----------------------------------------------------------------------+
# | UTILITY FUNCTIONS                                                    |
# +----------------------------------------------------------------------+
# read strategy files from data folder
def read_strategy(name, folders=[]):
    return read_yml(get_yaml(name, folders))


# read tokens in tokens.yml
def read_tokens():
    try:
        return read_yml(get_yaml('tokens'))
    except FileNotFoundError:
        raise MissingToken()


# get yaml path
def get_yaml(name, folders=[]):
    return get_path(name + '.yml', *folders)


# read yaml file
def read_yml(path):
    """read yaml and return dict"""
    with open(path, 'r') as yaml_file:
        yaml_dict = yaml.load(yaml_file)
        if yaml_dict is not None:
            config = yaml_dict
    return config


# save yaml file
def save_yaml(data, path):
    """save dict to yaml"""
    with open(path, 'w') as yaml_file:
        yaml_file.write(yaml.dump(data))


# get file in data folder
def get_path(*path):
    """get path of file in data folder (used mainly in strategy)"""
    data_folder = os.path.join(os.path.dirname(__file__), 'data')
    file_path = os.path.join(data_folder, *path)
    return file_path
