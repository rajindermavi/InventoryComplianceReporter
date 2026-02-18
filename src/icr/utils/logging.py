"""Logging utilities.

Provides a configurable logger factory that writes to both
console and a rotating log file.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(
    name: str,
    log_dir: str | Path = "logs",
    *,
    level: int = logging.INFO,
    max_bytes: int = 5_000_000,
    backup_count: int = 3,
) -> logging.Logger:
    """Create and return a configured logger.

    Args:
        name: Logger name, also used as the log file stem (e.g. ``"icr"``
              produces ``icr.log``).
        log_dir: Directory where log files are written.  Created if it does
                 not exist.
        level: Logging level (default ``INFO``).
        max_bytes: Max size per log file before rotation (default 5 MB).
        backup_count: Number of rotated backups to keep.

    Returns:
        A ``logging.Logger`` with console and file handlers attached.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (rotating)
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path / f"{name}.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
