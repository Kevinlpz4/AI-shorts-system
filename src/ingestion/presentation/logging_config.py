"""
Structured Logging — stdlib ``logging`` with JSON/text formatters.

Provides:
- ``RequestContextFilter``: injects ``request_id`` and ``correlation_id``
  into log records.
- ``JSONFormatter``: single-line JSON output for production.
- ``setup_logging()``: configures root logger.

Usage::

    from ingestion.presentation.logging_config import setup_logging
    setup_logging(log_level="INFO", log_format="json")
"""

from __future__ import annotations

import json
import logging
import sys


class RequestContextFilter(logging.Filter):
    """Inject request_id and correlation_id into log records.

    These fields are populated by middleware via ``request.state``.
    If not available (e.g., outside a request), defaults to ``"-"``.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request context fields to the log record.

        Args:
            record: The log record to enrich.

        Returns:
            Always True (record is never filtered out).
        """
        record.request_id = getattr(record, "request_id", "-")
        record.correlation_id = getattr(record, "correlation_id", "-")
        return True


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production environments.

    Outputs a single valid JSON line per log record with:
    - timestamp, level, message, logger name
    - request_id, correlation_id (from RequestContextFilter)
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a single JSON line.

        Args:
            record: The log record to format.

        Returns:
            A JSON string representing the log entry.
        """
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "correlation_id": getattr(record, "correlation_id", "-"),
        }
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
) -> None:
    """Configure root logger with appropriate formatter.

    Args:
        log_level: Python logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format — "json" for production, "text" for development.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestContextFilter())

    if log_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
        )

    root.handlers = [handler]
