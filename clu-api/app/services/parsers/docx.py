"""DOCX to text extraction using python-docx."""

import logging

logger = logging.getLogger(__name__)


def parse_docx(content: bytes) -> str:
    """Extract text from DOCX bytes using python-docx.

    Returns the full text content with paragraphs separated by newlines.
    """
    import io

    from docx import Document

    doc = Document(io.BytesIO(content))
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    if not paragraphs:
        raise ValueError("DOCX contains no extractable text")

    result = "\n\n".join(paragraphs)
    logger.info("Extracted %d paragraphs from DOCX (%d chars)", len(paragraphs), len(result))
    return result
