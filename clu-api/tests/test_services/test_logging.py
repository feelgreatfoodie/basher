"""Tests for structured logging configuration."""

import json
import logging

from app.logging_config import JSONFormatter, setup_logging


def test_json_formatter_basic():
    """JSONFormatter should produce valid JSON."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Test message", args=(), exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"
    assert parsed["logger"] == "test"
    assert "timestamp" in parsed


def test_json_formatter_with_extra_fields():
    """JSONFormatter should include known extra fields."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Scoped message", args=(), exc_info=None,
    )
    record.tenant_id = "tenant-123"
    record.project_id = "proj-456"
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["tenant_id"] == "tenant-123"
    assert parsed["project_id"] == "proj-456"


def test_json_formatter_without_extra_fields():
    """JSONFormatter should not include missing extra fields."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Plain message", args=(), exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert "tenant_id" not in parsed
    assert "project_id" not in parsed


def test_setup_logging_text_mode():
    """setup_logging with json_format=False should use text formatter."""
    setup_logging(json_format=False, level="DEBUG")
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert len(root.handlers) == 1
    assert not isinstance(root.handlers[0].formatter, JSONFormatter)


def test_setup_logging_json_mode():
    """setup_logging with json_format=True should use JSON formatter."""
    setup_logging(json_format=True, level="WARNING")
    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JSONFormatter)

    # Clean up: reset to text mode
    setup_logging(json_format=False, level="INFO")
