"""Auto-detect file type and route to the appropriate parser."""

import logging

from app.services.parsers.pdf import parse_pdf
from app.services.parsers.docx import parse_docx

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def detect_file_type(filename: str, content: bytes) -> str:
    """Detect file type from extension and magic bytes.

    Returns one of: 'txt', 'md', 'pdf', 'docx'
    """
    ext = _get_extension(filename)

    # Validate with magic bytes for binary formats
    if ext == "pdf" and not content[:5] == b"%PDF-":
        raise ValueError(f"File {filename} has .pdf extension but is not a valid PDF")
    if ext == "docx" and not content[:2] == b"PK":
        raise ValueError(f"File {filename} has .docx extension but is not a valid DOCX (ZIP)")

    # If extension is unknown, try magic bytes
    if ext == "unknown":
        if content[:5] == b"%PDF-":
            return "pdf"
        if content[:2] == b"PK":
            return "docx"
        return "txt"

    return ext


def detect_and_parse(filename: str, content: bytes) -> str:
    """Detect file type and extract text content.

    For PDF and DOCX files, extracts text using the appropriate parser.
    For text and markdown files, decodes as UTF-8.

    Returns plain text content suitable for transcript analysis.
    """
    file_type = detect_file_type(filename, content)
    logger.info("Detected file type '%s' for %s (%d bytes)", file_type, filename, len(content))

    if file_type == "pdf":
        return parse_pdf(content)
    elif file_type == "docx":
        return parse_docx(content)
    else:
        return content.decode("utf-8")


def _get_extension(filename: str) -> str:
    """Extract normalized extension from filename."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "pdf"
    if lower.endswith(".docx"):
        return "docx"
    if lower.endswith(".md"):
        return "md"
    if lower.endswith(".txt"):
        return "txt"
    return "unknown"
