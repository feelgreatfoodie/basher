"""Tests for incremental analysis service."""

import json
from unittest.mock import patch, MagicMock

import pytest

from app.services.incremental import _execute_incremental


MOCK_EXTRACTION = {
    "source": {"name": "test.txt"},
    "participants": [],
    "decisions": [],
    "actionItems": [],
    "requirements": [],
    "technicalConstraints": [],
    "openQuestions": [],
    "risks": [],
    "deferredItems": [],
}

MOCK_SYNTHESIS = {
    "summary": "Test summary",
    "conflicts": [],
    "gaps": [],
    "decisions": [],
    "requirements": [],
    "stakeholders": [],
    "actionItems": [],
}


@patch("app.services.incremental.synthesize_extractions")
@patch("app.services.incremental.find_semantic_conflicts", return_value=[])
@patch("app.services.incremental.index_extraction")
@patch("app.services.incremental.score_extraction", return_value=0.85)
@patch("app.services.incremental.extract_transcript")
def test_incremental_extracts_only_new(
    mock_extract, mock_score, mock_index, mock_conflicts, mock_synth, db
):
    """Incremental should only extract transcripts without existing extractions."""
    from app.models import Project, Transcript, Extraction, Analysis

    mock_synth.return_value = MOCK_SYNTHESIS.copy()

    # Create project with 2 transcripts
    project = Project(name="Test", tenant_id="tenant-test-001")
    db.add(project)
    db.commit()

    t1 = Transcript(
        project_id=project.id, filename="old.txt", content="old content",
        transcript_type="meeting", word_count=2, tenant_id="tenant-test-001",
    )
    t2 = Transcript(
        project_id=project.id, filename="new.txt", content="new content",
        transcript_type="meeting", word_count=2, tenant_id="tenant-test-001",
    )
    db.add_all([t1, t2])
    db.commit()

    # Add existing extraction for t1 (simulating a previous analysis)
    ext1 = Extraction(
        transcript_id=t1.id, data_json=json.dumps(MOCK_EXTRACTION),
        confidence=0.9, model_used="sonnet", tenant_id="tenant-test-001",
    )
    db.add(ext1)
    db.commit()

    # Create the analysis record
    analysis = Analysis(project_id=project.id, status="pending", tenant_id="tenant-test-001")
    db.add(analysis)
    db.commit()

    mock_extract.return_value = {
        "data": MOCK_EXTRACTION, "model_used": "sonnet", "cached": False,
    }

    # Call _execute_incremental directly (avoids SessionLocal patching issues)
    _execute_incremental(db, analysis.id, project.id)

    # Should have only extracted the new transcript
    assert mock_extract.call_count == 1
    call_kwargs = mock_extract.call_args[1]
    assert call_kwargs["filename"] == "new.txt"

    # Synthesis should have received ALL extractions (both old and new)
    assert mock_synth.call_count == 1
    synth_args = mock_synth.call_args[0]
    assert len(synth_args[0]) == 2  # 2 extraction data dicts

    # Analysis should be complete
    db.refresh(analysis)
    assert analysis.status == "complete"

    results = json.loads(analysis.results_json)
    assert results["incremental"] is True
    assert results["new_transcripts"] == 1
    assert results["total_transcripts"] == 2


@patch("app.services.incremental.synthesize_extractions")
@patch("app.services.incremental.find_semantic_conflicts", return_value=[])
@patch("app.services.incremental.index_extraction")
def test_incremental_no_new_transcripts_reruns_synthesis(
    mock_index, mock_conflicts, mock_synth, db
):
    """When all transcripts already extracted, skip extraction but re-run synthesis."""
    from app.models import Project, Transcript, Extraction, Analysis

    mock_synth.return_value = MOCK_SYNTHESIS.copy()

    project = Project(name="Test", tenant_id="tenant-test-001")
    db.add(project)
    db.commit()

    t1 = Transcript(
        project_id=project.id, filename="done.txt", content="done content",
        transcript_type="meeting", word_count=2, tenant_id="tenant-test-001",
    )
    db.add(t1)
    db.commit()

    ext1 = Extraction(
        transcript_id=t1.id, data_json=json.dumps(MOCK_EXTRACTION),
        confidence=0.9, model_used="sonnet", tenant_id="tenant-test-001",
    )
    db.add(ext1)
    db.commit()

    analysis = Analysis(project_id=project.id, status="pending", tenant_id="tenant-test-001")
    db.add(analysis)
    db.commit()

    _execute_incremental(db, analysis.id, project.id)

    # No extraction calls — all already done
    # Synthesis still called with existing data
    assert mock_synth.call_count == 1

    db.refresh(analysis)
    assert analysis.status == "complete"
    results = json.loads(analysis.results_json)
    assert results["new_transcripts"] == 0
