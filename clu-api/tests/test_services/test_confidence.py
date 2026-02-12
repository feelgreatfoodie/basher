from app.services.confidence import score_extraction, score_entity_confidence


def test_score_high_quality_extraction():
    """An extraction with quotes, participants with roles, and few open questions."""
    data = {
        "participants": [
            {"name": "Alice", "role": "PM"},
            {"name": "Bob", "role": "Engineer"},
        ],
        "decisions": [
            {"what": "Use REST", "decidedBy": ["Alice", "Bob"], "confidence": "high", "supportingQuotes": ["Let's use REST"]},
            {"what": "Use Postgres", "decidedBy": ["Alice"], "confidence": "high", "supportingQuotes": ["Postgres it is"]},
        ],
        "actionItems": [{"action": "Set up CI", "owner": "Bob"}],
        "requirements": [{"description": "Login", "type": "functional", "priority": "high", "mentionedBy": ["Alice"]}],
        "technicalConstraints": [{"constraint": "Must use Postgres"}],
        "openQuestions": [],
        "risks": [{"risk": "Tight timeline"}],
        "deferredItems": [{"item": "Admin panel"}],
    }

    score = score_extraction(data)
    assert 0.7 <= score <= 1.0, f"High quality extraction should score >= 0.7, got {score}"


def test_score_low_quality_extraction():
    """An extraction with no quotes, unknown participants, many open questions."""
    data = {
        "participants": [{"name": "Unknown"}],
        "decisions": [
            {"what": "Something", "decidedBy": []},
        ],
        "actionItems": [],
        "requirements": [],
        "technicalConstraints": [],
        "openQuestions": [
            {"question": "What?"},
            {"question": "When?"},
            {"question": "How?"},
        ],
        "risks": [],
        "deferredItems": [],
    }

    score = score_extraction(data)
    assert score < 0.5, f"Low quality extraction should score < 0.5, got {score}"


def test_score_empty_extraction():
    """An extraction with nothing extracted."""
    data = {
        "participants": [],
        "decisions": [],
        "actionItems": [],
        "requirements": [],
        "technicalConstraints": [],
        "openQuestions": [],
        "risks": [],
        "deferredItems": [],
    }

    score = score_extraction(data)
    assert 0.0 <= score <= 0.5, f"Empty extraction should score low, got {score}"


def test_score_entity_decision_high():
    entity = {"what": "Use REST", "decidedBy": ["Alice", "Bob"], "confidence": "high", "supportingQuotes": ["quote"]}
    score = score_entity_confidence(entity, "decisions")
    assert score >= 0.8


def test_score_entity_decision_low():
    entity = {"what": "Something", "decidedBy": [], "confidence": "low"}
    score = score_entity_confidence(entity, "decisions")
    assert score < 0.5


def test_score_entity_requirement():
    entity = {"description": "Login", "type": "functional", "priority": "high", "mentionedBy": ["Alice", "Bob"]}
    score = score_entity_confidence(entity, "requirements")
    assert score >= 0.7


def test_score_entity_action_item():
    entity = {"action": "Set up CI", "owner": "Bob", "deadline": "next Friday"}
    score = score_entity_confidence(entity, "actionItems")
    assert score >= 0.8


def test_score_range():
    """All scores must be between 0.0 and 1.0."""
    data = {
        "participants": [{"name": "A", "role": "PM"}],
        "decisions": [{"what": "X", "confidence": "high", "supportingQuotes": ["Y"], "decidedBy": ["A"]}],
        "actionItems": [],
        "requirements": [{"description": "Z", "type": "functional", "priority": "high", "mentionedBy": ["A", "B"]}],
        "technicalConstraints": [],
        "openQuestions": [{"question": "?"}],
        "risks": [],
        "deferredItems": [],
    }
    score = score_extraction(data)
    assert 0.0 <= score <= 1.0
