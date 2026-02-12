from unittest.mock import patch, MagicMock

from app.services.extractor import extract_transcript


@patch("app.services.extractor.set_cached_extraction")
@patch("app.services.extractor.get_cached_extraction", return_value=None)
@patch("app.services.extractor.anthropic.Anthropic")
def test_extract_transcript(mock_anthropic_cls, mock_cache_get, mock_cache_set):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"source": {"name": "test.txt"}, "participants": [], "decisions": [], "actionItems": [], "requirements": [], "technicalConstraints": [], "openQuestions": [], "risks": [], "deferredItems": []}')]
    mock_client.messages.create.return_value = mock_response

    result = extract_transcript(
        filename="test.txt",
        content="Alice: Let's use REST.\nBob: Agreed.",
        transcript_type="meeting",
        word_count=6,
    )

    assert "data" in result
    assert "model_used" in result
    assert result["data"]["source"]["name"] == "test.txt"
    assert result["cached"] is False
    mock_client.messages.create.assert_called_once()
    mock_cache_set.assert_called_once()


@patch("app.services.extractor.set_cached_extraction")
@patch("app.services.extractor.get_cached_extraction", return_value=None)
@patch("app.services.extractor.anthropic.Anthropic")
def test_extract_large_transcript_uses_opus(mock_anthropic_cls, mock_cache_get, mock_cache_set):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"source": {}, "participants": [], "decisions": [], "actionItems": [], "requirements": [], "technicalConstraints": [], "openQuestions": [], "risks": [], "deferredItems": []}')]
    mock_client.messages.create.return_value = mock_response

    result = extract_transcript(
        filename="big.txt",
        content="x " * 60000,
        transcript_type="meeting",
        word_count=60000,
    )

    # Large transcripts should use synthesis (Opus) model
    call_kwargs = mock_client.messages.create.call_args[1]
    assert "opus" in call_kwargs["model"] or "synthesis" in result["model_used"]


@patch("app.services.extractor.set_cached_extraction")
@patch("app.services.extractor.get_cached_extraction", return_value=None)
@patch("app.services.extractor.anthropic.Anthropic")
def test_extract_handles_code_block_response(mock_anthropic_cls, mock_cache_get, mock_cache_set):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='```json\n{"source": {}, "participants": [], "decisions": [], "actionItems": [], "requirements": [], "technicalConstraints": [], "openQuestions": [], "risks": [], "deferredItems": []}\n```')]
    mock_client.messages.create.return_value = mock_response

    result = extract_transcript("test.txt", "content", "meeting", 1)
    assert "data" in result


@patch("app.services.extractor.get_cached_extraction")
def test_extract_uses_cache_hit(mock_cache_get):
    """When cache has a result, skip the LLM call entirely."""
    cached_data = {
        "source": {"name": "cached.txt"},
        "participants": [],
        "decisions": [],
        "actionItems": [],
        "requirements": [],
        "technicalConstraints": [],
        "openQuestions": [],
        "risks": [],
        "deferredItems": [],
    }
    mock_cache_get.return_value = cached_data

    result = extract_transcript("cached.txt", "some content", "meeting", 10)

    assert result["cached"] is True
    assert result["data"]["source"]["name"] == "cached.txt"
