from .base import *
DEBUG = True

import logging.config
import os
from pathlib import Path
from datetime import datetime

os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

LOG_FILE_NAME = (
    f"{datetime.now():%Y_%m_%d-%I_%M_%S_%p}_"
    + f"_webserver"
)

LOG_DIR = os.path.join(os.path.join(BASE_DIR, "logs"))

GENERAL_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "color": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(asctime)s | %(levelname)s | %(message)s",
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        },
        "standard": {
            "format": "%(asctime)s | %(levelname)s | %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "color",
            "stream": "ext://sys.stdout",
        },
        "file_main": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": f"{LOG_DIR}/{LOG_FILE_NAME}.log",
            "mode": "a",
            "encoding": "utf-8",
        }
    },
    "loggers": {
        "webserver": {
            "handlers": ["console", "file_main"],
            "level": "INFO",
            "propagate": False,
        }
    },
}

logging.config.dictConfig(GENERAL_LOGGING_CONFIG)
