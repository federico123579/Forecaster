# ~~~~ console.py ~~~~
# forecaster.console
# ~~~~~~~~~~~~~~~~~~~~

import logging
import logging.config
import os.path

import rich
from foreanalyzer.utils import SingletonMeta


# ~ * LOGGER * ~
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'deafult': {
            'format':
                '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'deafult',
        },
        'rotating': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'deafult',
            'filename': os.path.join(
                os.path.dirname(__file__), 'logs', 'logfile.log'),
            'when': 'midnight',
            'backupCount': 3
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False
        },
        'forecaster': {
            'handlers': ['rotating'],
            'level': 'DEBUG',
            'propagate': False
        },
        'foreanalyzer': {
            'handlers': ['rotating'],
            'level': 'DEBUG',
            'propagate': False
        },
        'XTBApi': {
            'handlers': ['rotating'],
            'level': 'INFO',
            'propagate': False
        }
    }
})
LOGGER = logging.getLogger("forecaster")


# ~~~ * HIGH LEVEL CLASS * ~~~
class ForeCliConsole(metaclass=SingletonMeta):
    """console controller logger replacement
    this has four different levels of logging: debug, info, warn and error
    each of these has its own color and debug is printed only if verbose
    parameter is set to ON"""
    def __init__(self):
        self.console = rich.get_console()
        self.verbose = False

    def _color_markup(self, text, color):
        return f"[{color}]" + str(text) + f"[/{color}]"

    def log(self, text, prefix, *args, **kwargs):
        if prefix != None:
            text = prefix + " - " + text
        return self.console.log(text, *args, **kwargs)

    def write(self, text, *attrs):
        self.console.print(text, style=' '.join(attrs))

    def debug(self, text, prefix=None, level=1):
        logging.getLogger(f"forecaster.{prefix}").debug(text)
        if self.verbose >= level:
            #self.log(self._color_markup(text, "41"))
            self.log(self._color_markup(text, "green"), prefix)

    def info(self, text, prefix=None):
        logging.getLogger(f"forecaster.{prefix}").info(text)
        #self.log(self._color_markup(text, "62"))
        self.log(self._color_markup(text, "blue"), prefix)

    def warn(self, text, prefix=None):
        logging.getLogger(f"forecaster.{prefix}").warn(text)
        #self.log(self._color_markup(text, "228"))
        self.log(self._color_markup(text, "yellow"), prefix)

    def error(self, text, prefix=None):
        logging.getLogger(f"forecaster.{prefix}").error(text)
        #self.log(self._color_markup(text, "196"))
        self.log(self._color_markup(self._color_markup(text, "red"), "bold"), prefix)