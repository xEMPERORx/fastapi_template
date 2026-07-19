"""Application logger construction: console + rotating file handlers."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.logger.formatters import BeautifulFormatter, StructuredFormatter


def setup_logger(name: str = "app") -> logging.Logger:
    """Setup and configure the application logger."""
    Path("logs").mkdir(parents=True, exist_ok=True)

    app_logger = logging.getLogger(name)
    app_logger.setLevel(logging.DEBUG)
    app_logger.propagate = False
    app_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(BeautifulFormatter())
    app_logger.addHandler(console_handler)

    beautiful_file_handler = RotatingFileHandler(
        "logs/app_beautiful.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    beautiful_file_handler.setLevel(logging.DEBUG)
    beautiful_file_handler.setFormatter(BeautifulFormatter())
    app_logger.addHandler(beautiful_file_handler)

    json_file_handler = RotatingFileHandler(
        "logs/app_structured.json",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    json_file_handler.setLevel(logging.DEBUG)
    json_file_handler.setFormatter(StructuredFormatter())
    app_logger.addHandler(json_file_handler)

    error_file_handler = RotatingFileHandler(
        "logs/errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(BeautifulFormatter())
    app_logger.addHandler(error_file_handler)

    return app_logger


logger = setup_logger()
