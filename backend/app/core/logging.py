import logging
import sys
from typing import Optional

from pythonjsonlogger import jsonlogger


def configure_logging(level: Optional[str] = None) -> None:
    logger = logging.getLogger()
    logger.setLevel(level or logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(tenant_id)s %(errors)s"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]
