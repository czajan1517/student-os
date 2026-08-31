import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv


LOGGER_NAME = "studentos"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG_FILE = PROJECT_ROOT / "logs" / "studentos.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def _resolve_level(value: str) -> int:
    resolved = getattr(logging, value.upper(), None)
    return resolved if isinstance(resolved, int) else logging.INFO


def _resolve_log_file(value: str | Path) -> Path | None:
    if not str(value).strip():
        return None
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def configure_logging(
    *,
    level: str | None = None,
    log_file: str | Path | None = None,
    enable_console: bool = True,
) -> logging.Logger:
    """Configure StudentOS application logs without changing library loggers."""

    load_dotenv()
    configured_level = level or os.getenv("STUDENTOS_LOG_LEVEL", "INFO")
    configured_file = (
        log_file
        if log_file is not None
        else os.getenv("STUDENTOS_LOG_FILE", str(DEFAULT_LOG_FILE))
    )
    resolved_level = _resolve_level(configured_level)
    resolved_file = _resolve_log_file(configured_file)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(resolved_level)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, "studentos_managed", False):
            logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter(LOG_FORMAT)

    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.studentos_managed = True
        logger.addHandler(console_handler)

    if resolved_file is not None:
        resolved_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            resolved_file,
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.studentos_managed = True
        logger.addHandler(file_handler)

    logger.info(
        "logging_configured level=%s file=%s",
        logging.getLevelName(resolved_level),
        resolved_file or "disabled",
    )
    return logger
