import logging
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# Logger configuration
# ----------------------------------------------------------------------

LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str = "ai_trading", log_file: str | None = None, level: int = logging.INFO) -> logging.Logger:
    """Create or retrieve a configured logger.

    Parameters
    ----------
    name: str
        Logger name (usually ``__name__``).
    log_file: str | None, optional
        Path to a file where logs should also be written. If ``None`` only console
        output is used.
    level: int, default ``logging.INFO``
        Logging level.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        # Logger already configured – avoid duplicate handlers.
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# A module‑level default logger for quick imports
default_logger = get_logger()
