"""Confidence scoring for extractions (0.0 - 1.0 scale).

Scores each extraction based on quality signals:
- Quote quality: entities backed by direct quotes score higher
- Completeness: extractions with more entity types score higher
- Participant identification: named participants with roles score higher
- Ambiguity signals: presence of open questions lowers confidence slightly
"""

import logging

logger = logging.getLogger(__name__)


def score_extraction(extraction_data: dict) -> float:
    """Score an extraction's overall confidence from 0.0 to 1.0.

    Combines multiple quality signals into a single score.
    """
    scores = []

    scores.append(_score_quote_quality(extraction_data))
    scores.append(_score_completeness(extraction_data))
    scores.append(_score_participant_quality(extraction_data))
    scores.append(_score_ambiguity(extraction_data))

    # Weighted average: quote quality matters most
    weights = [0.35, 0.25, 0.20, 0.20]
    total = sum(s * w for s, w in zip(scores, weights))

    # Clamp to [0.0, 1.0]
    return round(max(0.0, min(1.0, total)), 3)


def _score_quote_quality(data: dict) -> float:
    """Score based on how many entities have supporting quotes."""
    decisions = data.get("decisions", [])
    if not decisions:
        return 0.5  # Neutral if no decisions

    quoted = sum(1 for d in decisions if d.get("supportingQuotes"))
    return min(1.0, quoted / max(len(decisions), 1))


def _score_completeness(data: dict) -> float:
    """Score based on how many entity types have data."""
    entity_types = [
        "participants", "decisions", "actionItems", "requirements",
        "technicalConstraints", "openQuestions", "risks", "deferredItems",
    ]
    populated = sum(1 for t in entity_types if data.get(t))
    return populated / len(entity_types)


def _score_participant_quality(data: dict) -> float:
    """Score based on participant identification quality."""
    participants = data.get("participants", [])
    if not participants:
        return 0.3  # Low if no participants identified

    with_roles = sum(1 for p in participants if p.get("role"))
    role_ratio = with_roles / len(participants)

    with_names = sum(1 for p in participants if p.get("name"))
    name_ratio = with_names / len(participants)

    return (role_ratio * 0.5) + (name_ratio * 0.5)


def _score_ambiguity(data: dict) -> float:
    """Score inversely based on ambiguity signals.

    More open questions relative to decisions = more ambiguity = lower score.
    """
    open_questions = len(data.get("openQuestions", []))
    decisions = len(data.get("decisions", []))
    requirements = len(data.get("requirements", []))

    total_concrete = decisions + requirements
    if total_concrete == 0:
        return 0.3  # Low confidence if nothing concrete extracted

    # Ratio of unresolved to resolved — lower is better
    ambiguity_ratio = open_questions / (total_concrete + open_questions)
    return 1.0 - ambiguity_ratio


def score_entity_confidence(entity: dict, entity_type: str) -> float:
    """Score confidence for a single entity based on its quality signals."""
    if entity_type == "decisions":
        score = 0.5
        if entity.get("supportingQuotes"):
            score += 0.2
        confidence = entity.get("confidence", "medium")
        if confidence == "high":
            score += 0.2
        elif confidence == "low":
            score -= 0.2
        if len(entity.get("decidedBy", [])) > 1:
            score += 0.1
        return max(0.0, min(1.0, score))

    elif entity_type == "requirements":
        score = 0.5
        priority = entity.get("priority", "medium")
        if priority == "high":
            score += 0.15
        if len(entity.get("mentionedBy", [])) > 1:
            score += 0.2
        if entity.get("type"):
            score += 0.1
        return max(0.0, min(1.0, score))

    elif entity_type == "actionItems":
        score = 0.5
        if entity.get("owner"):
            score += 0.2
        if entity.get("deadline"):
            score += 0.15
        if entity.get("action"):
            score += 0.15
        return max(0.0, min(1.0, score))

    # Default for other entity types
    return 0.5
