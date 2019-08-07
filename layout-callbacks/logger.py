import logging
from colorlog import ColoredFormatter
from config.const import LOG_LEVEL, LOG_FORMAT, LOG_NAME_FORMAT, Handler
import datetime


def logger(name):
    """
    Usage:
    from logger import Logger
    logger = Logger(name)
    """
    filename = datetime.datetime.now().strftime(LOG_NAME_FORMAT)
    try:
        logging.basicConfig(filename='logs/'+filename, level=LOG_LEVEL)
    except:
        pass
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logging.root.setLevel(LOG_LEVEL)
    formatter = ColoredFormatter(LOG_FORMAT)
    if Handler is None:
        stream = logging.StreamHandler()
    else:
        stream = Handler
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    return logger


