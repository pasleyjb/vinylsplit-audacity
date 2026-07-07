"""Application-wide logging configuration."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from vinylsplit import __app_name__, __version__

_DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _default_log_directory() -> Path:
    """Return the platform-appropriate directory for log files."""
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Local" / "VinylSplit"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Logs" / "VinylSplit"
    else:
        base = Path.home() / ".local" / "state" / "vinylsplit"

    base.mkdir(parents=True, exist_ok=True)
    return base


def configure_logging(
    *,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_directory: Path | None = None,
) -> None:
    """Configure root and application loggers.

    Args:
        level: Minimum log level for console and file handlers.
        log_to_file: When True, also write logs to a rotating file.
        log_directory: Optional override for the log file directory.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers when the app is restarted in the same process.
    if root_logger.handlers:
        return

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(
        logging.Formatter(_DEFAULT_LOG_FORMAT, datefmt=_DEFAULT_DATE_FORMAT)
    )
    root_logger.addHandler(console_handler)

    if log_to_file:
        directory = log_directory or _default_log_directory()
        log_path = directory / "vinylsplit.log"
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=1_048_576,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(_DEFAULT_LOG_FORMAT, datefmt=_DEFAULT_DATE_FORMAT)
        )
        root_logger.addHandler(file_handler)

    app_logger = logging.getLogger("vinylsplit")
    app_logger.info("Starting %s v%s", __app_name__, __version__)
