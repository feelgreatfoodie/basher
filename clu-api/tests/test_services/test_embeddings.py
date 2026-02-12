from unittest.mock import patch, MagicMock

from app.services.embeddings import (
    _entity_to_text,
    _entity_id,
    index_extraction,
    find_similar_entities,
)


def test_entity_to_text_decision():
    entity = {"what": "Use REST", "decidedBy": ["Alice", "Bob"]}
    text = _entity_to_text(entity, "decisions")
    assert "Use REST" in text
    assert "Alice" in text


def test_entity_to_text_requirement():
    entity = {"description": "User login", "type": "functional"}
    text = _entity_to_text(entity, "requirements")
    assert "User login" in text
    assert "functional" in text


def test_entity_to_text_action_item():
    entity = {"action": "Set up CI", "owner": "Bob"}
    text = _entity_to_text(entity, "actionItems")
    assert "Set up CI" in text
    assert "Bob" in text


def test_entity_id_stable():
    """Same input should always produce the same ID."""
    entity = {"what": "Use REST"}
    id1 = _entity_id("source.txt", "decisions", entity)
    id2 = _entity_id("source.txt", "decisions", entity)
    assert id1 == id2


def test_entity_id_different_for_different_sources():
    entity = {"what": "Use REST"}
    id1 = _entity_id("source1.txt", "decisions", entity)
    id2 = _entity_id("source2.txt", "decisions", entity)
    assert id1 != id2


@patch("app.services.embeddings._get_client")
def test_index_extraction(mock_get_client):
    mock_collection = MagicMock()
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_get_client.return_value = mock_client

    extraction = {
        "source": {"name": "meeting.txt"},
        "decisions": [{"what": "Use REST", "decidedBy": ["Alice"]}],
        "requirements": [{"description": "Login", "type": "functional"}],
        "actionItems": [],
        "risks": [],
        "openQuestions": [],
        "technicalConstraints": [],
    }

    count = index_extraction(extraction, "project-123")
    assert count == 2  # 1 decision + 1 requirement
    mock_collection.upsert.assert_called_once()


@patch("app.services.embeddings._get_client")
def test_index_empty_extraction(mock_get_client):
    mock_collection = MagicMock()
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_get_client.return_value = mock_client

    extraction = {
        "source": {"name": "empty.txt"},
        "decisions": [],
        "requirements": [],
        "actionItems": [],
        "risks": [],
        "openQuestions": [],
        "technicalConstraints": [],
    }

    count = index_extraction(extraction, "project-123")
    assert count == 0
    mock_collection.upsert.assert_not_called()


@patch("app.services.embeddings._get_client")
def test_find_similar_entities(mock_get_client):
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["Decision: Use REST"]],
        "metadatas": [[{"source": "a.txt", "entity_type": "decisions", "entity_json": '{"what": "Use REST"}'}]],
        "distances": [[0.15]],
    }

    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection
    mock_get_client.return_value = mock_client

    results = find_similar_entities("Use REST API", "project-123")
    assert len(results) == 1
    assert results[0]["similarity"] == 0.85  # 1.0 - 0.15
    assert results[0]["source"] == "a.txt"
