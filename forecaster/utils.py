"""
forecaster.utils
~~~~~~~~~~~~~~

Contains all the utils of module and Abstract classes.
"""

import configparser
import json
import os
import os.path
import sys

import termcolor
import yaml
from forecaster.exceptions import MissingToken


# +----------------------------------------------------------------------+
# | UTILITY FUNCTIONS                                                    |
# +----------------------------------------------------------------------+
# read strategy files from config folder
def read_strategy(name, folders=[]):
    return read_yml(get_yaml(name, folders))


# read strategy files from config folder
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
    return get_path(*folders, name + '.yml')


# get json path
def get_json(name, folders=[]):
    return get_path(*folders, name + '.json')


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
def get_conf(filename='config'):
    config = configparser.ConfigParser()
    path = os.path.join(os.path.dirname(__file__), 'config', filename + '.ini')
    config.read(path)
    return config


# save configuration
def save_conf(config, filename):
    path = os.path.join(os.path.dirname(__file__), 'config', filename + '.ini')
    with open(path, 'w') as configfile:
        config.write(configfile)


# get file in config folder
def get_path(*path):
    """get path of file in config folder (used mainly in strategy)"""
    config_folder = os.path.join(os.path.dirname(__file__), 'config')
    file_path = os.path.join(config_folder, *path)
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


class CLIConfig(object):
    def __init__(self, argument, data_file, config, overwrite=True):
        self.ARG = argument
        self.FILE = data_file
        self.CONFIG = config
        self.OVER = overwrite
        self.queries = []
        self.entries = []

    def add_query(self, name_var, query):
        """add query to ask for entries"""
        query_encapsuled = (name_var, query)
        self.queries.append(query_encapsuled)

    def add_query_insert(self, name_var, query):
        query = "please insert your {}".format(query)
        self.add_query(name_var, query)

    def run(self):
        """wrap tun to exit if Ctrl-C"""
        try:
            self._run()
        except KeyboardInterrupt:
            sys.stdout.write("\rexited...")

    def _run(self):
        """inner run function"""
        CLI.print_bold("forecaster CONFIG mode enabled:")
        CLI.print_bold("ARGUMENT - {}:".format(self.ARG))
        self._ask_queries()  # ask queries
        self._save_config()  # save entries in config
        print("config saved")

    def _ask_queries(self):
        """ask every queries and save entries"""
        for query in self.queries:
            entry = input(CLI.colored("{}:\n".format(query[1]), 'yellow'))
            entry_encapsuled = (query[0], entry)
            self.entries.append(entry_encapsuled)

    def _save_config(self):
        if self.CONFIG not in ('json', 'ini'):
            raise ValueError("CONFIG type not exists")
        if self.CONFIG == 'json':
            path = get_json(self.FILE)
            if not self.OVER:
                config = read_json(path)
            else:
                config = {}
            for entry in self.entries:
                config[entry[0]] = entry[1]
            save_json(config, path)
        elif self.CONFIG == 'ini':
            if not self.OVER:
                config = get_conf(self.FILE)
            else:
                config = {}
            for entry in self.entries:
                config[entry[0][0]][entry[0][1]] = entry[1]
            save_conf(config, self.FILE)
