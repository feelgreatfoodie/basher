from unittest.mock import patch, MagicMock

from app.services.synthesizer import synthesize_extractions


@patch("app.services.synthesizer.set_cached_synthesis")
@patch("app.services.synthesizer.get_cached_synthesis", return_value=None)
@patch("app.services.synthesizer.anthropic.Anthropic")
def test_synthesize_extractions(mock_anthropic_cls, mock_cache_get, mock_cache_set):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"summary": {"totalTranscripts": 2, "conflictsFound": 1}, "conflicts": [{"topic": "API protocol"}], "gaps": [], "decisions": [], "requirements": [], "stakeholders": [], "actionItems": []}')]
    mock_client.messages.create.return_value = mock_response

    extractions = [
        {"source": {"name": "meeting1.txt"}, "decisions": [{"what": "Use REST"}]},
        {"source": {"name": "meeting2.txt"}, "decisions": [{"what": "Use GraphQL"}]},
    ]

    result = synthesize_extractions(extractions)
    assert "summary" in result
    assert "conflicts" in result
    mock_client.messages.create.assert_called_once()
    mock_cache_set.assert_called_once()


@patch("app.services.synthesizer.set_cached_synthesis")
@patch("app.services.synthesizer.get_cached_synthesis", return_value=None)
@patch("app.services.synthesizer.anthropic.Anthropic")
def test_synthesize_with_semantic_conflicts(mock_anthropic_cls, mock_cache_get, mock_cache_set):
    """When semantic conflicts are provided, they should be passed to the prompt."""
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"summary": {}, "conflicts": [], "gaps": [], "decisions": [], "requirements": [], "stakeholders": [], "actionItems": []}')]
    mock_client.messages.create.return_value = mock_response

    extractions = [{"source": {"name": "a.txt"}, "decisions": []}]
    semantic_conflicts = [
        {
            "entity_a": {"text": "Use REST", "source": "a.txt"},
            "entity_b": {"text": "Use GraphQL", "source": "b.txt"},
            "similarity": 0.85,
        }
    ]

    result = synthesize_extractions(extractions, semantic_conflicts=semantic_conflicts)
    assert "summary" in result

    # Semantic conflicts should appear in the prompt
    call_args = mock_client.messages.create.call_args[1]
    prompt_text = call_args["messages"][0]["content"]
    assert "Semantic similarity hints" in prompt_text


@patch("app.services.synthesizer.get_cached_synthesis")
def test_synthesize_uses_cache_hit(mock_cache_get):
    """When cache has a result, skip the LLM call entirely."""
    cached = {
        "summary": {"totalTranscripts": 1},
        "conflicts": [],
        "gaps": [],
        "decisions": [],
        "requirements": [],
        "stakeholders": [],
        "actionItems": [],
    }
    mock_cache_get.return_value = cached

    result = synthesize_extractions([{"source": {"name": "a.txt"}}])
    assert result == cached
