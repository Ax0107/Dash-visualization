import logging
from colorlog import ColoredFormatter
from config.const import LOG_LEVEL, LOG_FORMAT, LOG_NAME_FORMAT, Handler
import datetime


class Logger(object):
    """
    Usage:
    from logger import Logger
    logger = Logger(name).logger
    """
    def __init__(self, name):
        filename = datetime.datetime.now().strftime(LOG_NAME_FORMAT)
        logging.basicConfig(filename='logs/'+filename, level=LOG_LEVEL)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVEL)
        logging.root.setLevel(LOG_LEVEL)
        formatter = ColoredFormatter(LOG_FORMAT)
        if Handler is None:
            stream = logging.StreamHandler()
        else:
            stream = Handler
        stream.setLevel(LOG_LEVEL)
        stream.setFormatter(formatter)
        self.logger.addHandler(stream)


