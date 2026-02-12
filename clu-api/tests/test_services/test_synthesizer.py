from unittest.mock import patch, MagicMock

from app.services.synthesizer import synthesize_extractions


@patch("app.services.synthesizer.anthropic.Anthropic")
def test_synthesize_extractions(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    synthesis_result = {
        "summary": {"totalTranscripts": 2, "conflictsFound": 1},
        "conflicts": [{"topic": "API protocol"}],
        "gaps": [],
        "decisions": [],
        "requirements": [],
        "stakeholders": [],
        "actionItems": [],
    }

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
