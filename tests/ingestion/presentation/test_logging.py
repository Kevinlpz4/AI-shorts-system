"""
Tests for Structured Logging Configuration (REQ-F8).

Validates:
- setup_logging configures root logger with correct level
- setup_logging configures root logger with JSON formatter
- setup_logging configures root logger with text formatter
- JSONFormatter produces valid JSON with required fields
- RequestContextFilter adds request_id and correlation_id defaults
"""

from __future__ import annotations

import json
import logging

import pytest

from ingestion.presentation.logging_config import (
    JSONFormatter,
    RequestContextFilter,
    setup_logging,
)


class TestSetupLogging:
    """Test setup_logging root logger configuration."""

    def test_setup_logging_configures_root(self):
        """setup_logging should set root logger to the specified level."""
        setup_logging(log_level="INFO", log_format="text")
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_setup_logging_debug_level(self):
        """setup_logging should support DEBUG level."""
        setup_logging(log_level="DEBUG", log_format="text")
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_setup_logging_json_format(self):
        """setup_logging with json format should use JSONFormatter."""
        setup_logging(log_level="INFO", log_format="json")
        root = logging.getLogger()
        assert len(root.handlers) == 1
        handler = root.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)

    def test_setup_logging_text_format(self):
        """setup_logging with text format should use standard Formatter."""
        setup_logging(log_level="INFO", log_format="text")
        root = logging.getLogger()
        assert len(root.handlers) == 1
        handler = root.handlers[0]
        assert isinstance(handler.formatter, logging.Formatter)
        # Should NOT be JSONFormatter
        assert not isinstance(handler.formatter, JSONFormatter)

    def test_setup_logging_adds_request_context_filter(self):
        """setup_logging should attach RequestContextFilter to handler."""
        setup_logging(log_level="INFO", log_format="text")
        root = logging.getLogger()
        handler = root.handlers[0]
        filter_names = [type(f).__name__ for f in handler.filters]
        assert "RequestContextFilter" in filter_names


class TestJSONFormatter:
    """Test JSONFormatter output."""

    def test_json_formatter_output(self):
        """JSONFormatter should produce valid JSON with required fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["message"] == "test message"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert "timestamp" in parsed

    def test_json_formatter_includes_context_fields(self):
        """JSONFormatter should include request_id and correlation_id."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="warning",
            args=(),
            exc_info=None,
        )
        # Simulate RequestContextFilter having run
        record.request_id = "req-123"
        record.correlation_id = "corr-456"

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["request_id"] == "req-123"
        assert parsed["correlation_id"] == "corr-456"

    def test_json_formatter_defaults_for_missing_context(self):
        """JSONFormatter should default to '-' when context fields missing."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="error",
            args=(),
            exc_info=None,
        )
        # No request_id or correlation_id set
        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["request_id"] == "-"
        assert parsed["correlation_id"] == "-"


class TestRequestContextFilter:
    """Test RequestContextFilter field injection."""

    def test_request_context_filter_adds_fields(self):
        """RequestContextFilter should add request_id and correlation_id."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None,
        )
        filt = RequestContextFilter()
        result = filt.filter(record)

        assert result is True  # Never filters out
        assert record.request_id == "-"
        assert record.correlation_id == "-"

    def test_request_context_filter_preserves_existing(self):
        """RequestContextFilter should not overwrite existing values."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None,
        )
        record.request_id = "my-request-id"
        record.correlation_id = "my-correlation-id"

        filt = RequestContextFilter()
        result = filt.filter(record)

        assert result is True
        assert record.request_id == "my-request-id"
        assert record.correlation_id == "my-correlation-id"
