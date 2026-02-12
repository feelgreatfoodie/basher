"""PDF to text extraction using PyMuPDF (fitz)."""

import logging

logger = logging.getLogger(__name__)


def parse_pdf(content: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF.

    Returns the full text content of the PDF with pages separated by newlines.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=content, filetype="pdf")
    pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        if text.strip():
            pages.append(text)
    doc.close()

    if not pages:
        raise ValueError("PDF contains no extractable text")

    result = "\n\n".join(pages)
    logger.info("Extracted %d pages from PDF (%d chars)", len(pages), len(result))
    return result
