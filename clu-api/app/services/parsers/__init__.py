"""File parsers for PDF, DOCX, and plain text ingestion."""

from app.services.parsers.detector import detect_and_parse

__all__ = ["detect_and_parse"]
