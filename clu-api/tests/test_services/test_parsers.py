"""Tests for file parsers (PDF, DOCX, text detection)."""

from unittest.mock import patch, MagicMock

from app.services.parsers.detector import detect_file_type, detect_and_parse, _get_extension


def test_get_extension_pdf():
    assert _get_extension("meeting.pdf") == "pdf"
    assert _get_extension("Meeting.PDF") == "pdf"


def test_get_extension_docx():
    assert _get_extension("notes.docx") == "docx"
    assert _get_extension("Notes.DOCX") == "docx"


def test_get_extension_text():
    assert _get_extension("meeting.txt") == "txt"
    assert _get_extension("notes.md") == "md"


def test_get_extension_unknown():
    assert _get_extension("file.csv") == "unknown"
    assert _get_extension("noext") == "unknown"


def test_detect_file_type_by_extension():
    assert detect_file_type("test.txt", b"hello") == "txt"
    assert detect_file_type("test.md", b"# header") == "md"


def test_detect_file_type_pdf_valid():
    assert detect_file_type("test.pdf", b"%PDF-1.4 content") == "pdf"


def test_detect_file_type_pdf_invalid_magic():
    """PDF extension with wrong magic bytes should raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="not a valid PDF"):
        detect_file_type("test.pdf", b"not a pdf")


def test_detect_file_type_docx_valid():
    assert detect_file_type("test.docx", b"PK\x03\x04 content") == "docx"


def test_detect_file_type_docx_invalid_magic():
    """DOCX extension with wrong magic bytes should raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="not a valid DOCX"):
        detect_file_type("test.docx", b"not a docx")


def test_detect_file_type_unknown_ext_pdf_magic():
    """Unknown extension but PDF magic bytes should detect as pdf."""
    assert detect_file_type("unknown_file", b"%PDF-1.4 content") == "pdf"


def test_detect_file_type_unknown_ext_docx_magic():
    """Unknown extension but ZIP magic bytes should detect as docx."""
    assert detect_file_type("unknown_file", b"PK\x03\x04 content") == "docx"


def test_detect_file_type_unknown_ext_text_fallback():
    """Unknown extension and no magic bytes should fall back to txt."""
    assert detect_file_type("unknown_file", b"plain text content") == "txt"


def test_detect_and_parse_text():
    content = b"Alice: Let's discuss the API."
    result = detect_and_parse("meeting.txt", content)
    assert result == "Alice: Let's discuss the API."


def test_detect_and_parse_markdown():
    content = b"# Meeting Notes\n\nSome notes here."
    result = detect_and_parse("notes.md", content)
    assert "Meeting Notes" in result


@patch("app.services.parsers.detector.parse_pdf")
def test_detect_and_parse_pdf(mock_parse_pdf):
    mock_parse_pdf.return_value = "Extracted PDF text"
    result = detect_and_parse("doc.pdf", b"%PDF-1.4 fake pdf")
    assert result == "Extracted PDF text"
    mock_parse_pdf.assert_called_once_with(b"%PDF-1.4 fake pdf")


@patch("app.services.parsers.detector.parse_docx")
def test_detect_and_parse_docx(mock_parse_docx):
    mock_parse_docx.return_value = "Extracted DOCX text"
    result = detect_and_parse("doc.docx", b"PK\x03\x04 fake docx")
    assert result == "Extracted DOCX text"
    mock_parse_docx.assert_called_once_with(b"PK\x03\x04 fake docx")


def test_parse_pdf_extracts_pages():
    """Test PDF parser extracts text from multiple pages."""
    import sys
    from app.services.parsers.pdf import parse_pdf

    mock_fitz = MagicMock()
    mock_doc = MagicMock()
    mock_doc.__len__ = lambda self: 2
    mock_page1 = MagicMock()
    mock_page1.get_text.return_value = "Page 1 content"
    mock_page2 = MagicMock()
    mock_page2.get_text.return_value = "Page 2 content"
    mock_doc.load_page.side_effect = [mock_page1, mock_page2]
    mock_fitz.open.return_value = mock_doc

    with patch.dict(sys.modules, {"fitz": mock_fitz}):
        result = parse_pdf(b"%PDF-fake")
    assert "Page 1 content" in result
    assert "Page 2 content" in result
    mock_doc.close.assert_called_once()


def test_parse_pdf_empty_raises():
    """PDF with no extractable text should raise ValueError."""
    import sys
    import pytest
    from app.services.parsers.pdf import parse_pdf

    mock_fitz = MagicMock()
    mock_doc = MagicMock()
    mock_doc.__len__ = lambda self: 1
    mock_page = MagicMock()
    mock_page.get_text.return_value = "   "
    mock_doc.load_page.return_value = mock_page
    mock_fitz.open.return_value = mock_doc

    with patch.dict(sys.modules, {"fitz": mock_fitz}):
        with pytest.raises(ValueError, match="no extractable text"):
            parse_pdf(b"%PDF-fake")
