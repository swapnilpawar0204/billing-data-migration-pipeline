import logging
import sys
from contextvars import ContextVar

from app.config.settings import settings

# Set per request by the middleware in app.main so every log line can be
# correlated with the request that produced it.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def _get_log_level(level: str) -> int:
    return getattr(logging, (level or "INFO").upper(), logging.INFO)


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a reusable logger configured from application settings."""
    logger = logging.getLogger(name or "billing_data_migration")
    logger.setLevel(_get_log_level(settings.log_level))

    if logger.handlers:
        return logger

    logger.propagate = False
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_RequestIdFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    return logger


logger = get_logger(__name__)
