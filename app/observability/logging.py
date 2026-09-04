import logging
import sys

from pythonjsonlogger.json import (
    JsonFormatter,
)


def configure_logging():

    logger = logging.getLogger()

    logger.setLevel(
        logging.INFO
    )

    if logger.handlers:
        return

    handler = logging.StreamHandler(
        sys.stdout
    )

    formatter = JsonFormatter(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s"
    )

    handler.setFormatter(
        formatter
    )

    logger.addHandler(
        handler
    )