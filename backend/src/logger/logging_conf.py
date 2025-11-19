"""
Logging configuration module.
"""
import os
from logging.config import dictConfig  # pylint: disable=import-error, no-name-in-module
from config.settings import LOG_FILE, LOG_JSON, LOG_LEVEL


def get_formatter():
    """
    Get the appropriate log formatter based on settings.
    Returns:
        _type_: _formatter name_
    """
    return "json" if LOG_JSON else "standard"


def configure_logging():
    """
    Configure logging for the application.
    Sets up console and file handlers with appropriate formatters.
    """
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": get_formatter(),
            "stream": "ext://sys.stdout",
            "filters": ["exclude_httpx"],
        }
    }

    if LOG_FILE:
        if not os.path.exists(os.path.dirname(LOG_FILE)):
            os.makedirs(os.path.dirname(LOG_FILE))
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_FILE,
            "level": LOG_LEVEL,
            "formatter": "json",
            "maxBytes": 5*1024*1024,
            "backupCount": 5,
            "encoding": "utf-8"
        }

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "exclude_httpx": {
                "()": "logger.logger.ExcludeHttpxFilter"
            },
        },

        "formatters": {
            "standard": {
                "format": "[%(levelname)s]: %(asctime)s — %(filename)s:%(lineno)d — %(message)s",
                "datefmt": "%d-%m-%Y %H:%M:%S",
            },
            "json": {
                "()": "logger.formatters.JSONFormatter",
            },
        },

        "handlers": handlers,

        "loggers": {
            "": {
                "handlers": list(handlers.keys()),
                "level": LOG_LEVEL,
                "propagate": False,
            }
        }
    })
