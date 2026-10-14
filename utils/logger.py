"""
نظام التسجيل — بدون emojis
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


LOG_FILE = Path(__file__).parent.parent / "logs.txt"


def setup_logger(name="YouTubeMediaHub"):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    try:
        fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        print("Log file error: {}".format(e))
    
    try:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    except Exception:
        pass
    
    return logger


app_logger = setup_logger()


def log_separator(message=""):
    sep = "=" * 60
    app_logger.info("{} {} {}".format(sep, message, sep))


def log_startup():
    log_separator("Startup - {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


def log_shutdown():
    log_separator("Shutdown - {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))