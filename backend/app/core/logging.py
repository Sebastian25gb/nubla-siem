import logging
import sys
from pythonjsonlogger import jsonlogger

def configure_logging(level: str | None = None):
    logger = logging.getLogger()
    logger.setLevel(level or logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]