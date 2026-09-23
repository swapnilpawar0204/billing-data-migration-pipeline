import logging
import sys

from app.config.settings import settings


def _get_log_level(level: str) -> int:
    normalized = (level or "INFO").upper()
    return getattr(logging, normalized, logging.INFO)


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a reusable logger configured from application settings."""
    logger_name = name or "cloud_billing_data_migration"
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        logger.setLevel(_get_log_level(settings.log_level))
        return logger

    logger.setLevel(_get_log_level(settings.log_level))
    logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)

    return logger


logger = get_logger(__name__)  # Structured application logger configuration (Phase 2)
