import logging.config
import os.path

__AUTHOR__ = "Federico Lolli"
__VERSION__ = "v0.1a0"

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'deafult': {
            'format':
                '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'mov_form': {
            'format': '%(asctime)s - %(message)s'
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
                os.path.dirname(__file__), 'logs/logfile.log'),
            'when': 'midnight',
            'backupCount': 3
        },
        'movs_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'mov_form',
            'filename': os.path.join(
                os.path.dirname(__file__), 'logs/movlist.log'),
            'mode': 'w'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'CRITICAL',
            'propagate': True
        },
        'forecaster': {
            'handlers': ['rotating'],
            'level': 'CRITICAL'
        },
        'mover': {
            'handlers': ['movs_handler'],
            'level': 'DEBUG'
        }
    }
})
