import logging
import sys

def GetLogger():
    FORMAT='%(levelname)s: %(asctime)s: [%(filename)s:%(lineno)d] %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt='%m-%d %H:%M:%S',
            stream=sys.stdout)
    logger = logging.getLogger()
    return logger
