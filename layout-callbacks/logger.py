import logging
from colorlog import ColoredFormatter
from config.const import LOG_LEVEL, LOG_FORMAT
import datetime


class Logger(object):
    def __init__(self, name, log_level, log_format):
        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")
        logging.basicConfig(filename=filename, level=log_level)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        logging.root.setLevel(log_level)
        formatter = ColoredFormatter(log_format)
        stream = logging.StreamHandler()
        stream.setLevel(log_level)
        stream.setFormatter(formatter)
        self.logger.addHandler(stream)


logger = Logger('redis', LOG_LEVEL, LOG_FORMAT).logger
