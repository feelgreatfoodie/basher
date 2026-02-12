from unittest.mock import patch, MagicMock

from app.services.prd_generator import generate_prd


@patch("app.services.prd_generator.anthropic.Anthropic")
def test_generate_prd(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="# PRD\n\n## User Stories\n\n1. As a user...")]
    mock_client.messages.create.return_value = mock_response

    analysis = {
        "summary": {"totalTranscripts": 2},
        "requirements": [{"description": "User login", "priority": "high", "consensus": 3}],
        "conflicts": [],
    }

    result = generate_prd(analysis)
    assert "PRD" in result
    assert "User Stories" in result
    mock_client.messages.create.assert_called_once()
