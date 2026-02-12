"""Tests for the recovery service."""

import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.models import Analysis, Transcript, Extraction
from app.services.recovery import recover_analysis, _resume_from_checkpoint, CHECKPOINTS


def test_checkpoints_are_ordered():
    """Checkpoint list should follow the pipeline order."""
    assert CHECKPOINTS == [
        "extraction_complete",
        "indexing_complete",
        "synthesis_complete",
        "prd_complete",
        "complete",
    ]


@patch("app.services.recovery.SessionLocal")
def test_recover_analysis_not_found(mock_session_cls):
    """recover_analysis should handle missing analysis gracefully."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_session_cls.return_value = mock_db

    # Should not raise — writes error to DB
    recover_analysis("nonexistent-id")
    mock_db.close.assert_called_once()


@patch("app.services.recovery.SessionLocal")
def test_recover_analysis_wrong_status(mock_session_cls):
    """recover_analysis should reject non-failed analyses."""
    mock_db = MagicMock()
    analysis = MagicMock()
    analysis.id = "test-id"
    analysis.status = "complete"  # Not failed

    # First call returns the analysis, second call (in except) also returns it
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        analysis, analysis,
    ]
    mock_session_cls.return_value = mock_db

    recover_analysis("test-id")

    # Should have set status back to failed with error message
    assert analysis.status == "failed"
    assert "not 'failed'" in analysis.error_message
    mock_db.close.assert_called_once()


@patch("app.services.recovery.synthesize_extractions")
@patch("app.services.recovery.find_semantic_conflicts")
@patch("app.services.recovery.index_extraction")
def test_resume_from_extraction_checkpoint(
    mock_index, mock_conflicts, mock_synthesize, db
):
    """Resuming from extraction_complete should skip extraction, run indexing + synthesis."""
    from tests.conftest import TEST_TENANT_ID

    # Create project, transcript, extraction, and failed analysis
    from app.models import Project
    project = Project(name="Recovery Test", tenant_id=TEST_TENANT_ID)
    db.add(project)
    db.commit()
    db.refresh(project)

    transcript = Transcript(
        project_id=project.id,
        filename="test.txt",
        content="Alice: Test content",
        transcript_type="meeting",
        word_count=3,
        tenant_id=TEST_TENANT_ID,
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)

    extraction = Extraction(
        transcript_id=transcript.id,
        data_json=json.dumps({"decisions": [{"text": "Use REST"}]}),
        confidence=0.85,
        model_used="test-model",
        tenant_id=TEST_TENANT_ID,
    )
    db.add(extraction)
    db.commit()

    analysis = Analysis(
        project_id=project.id,
        status="recovering",
        last_checkpoint="extraction_complete",
        tenant_id=TEST_TENANT_ID,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    mock_conflicts.return_value = []
    mock_synthesize.return_value = {"summary": {"totalTranscripts": 1}, "conflicts": []}

    _resume_from_checkpoint(db, analysis, "extraction_complete")

    assert analysis.status == "complete"
    assert analysis.last_checkpoint == "complete"
    assert analysis.results_json is not None
    mock_index.assert_called_once()
    mock_synthesize.assert_called_once()


@patch("app.services.recovery.generate_prd")
@patch("app.services.recovery.synthesize_extractions")
@patch("app.services.recovery.find_semantic_conflicts")
@patch("app.services.recovery.index_extraction")
def test_resume_with_prd_requested(
    mock_index, mock_conflicts, mock_synthesize, mock_prd, db
):
    """Recovery should generate PRD if prd_requested flag is in results."""
    from tests.conftest import TEST_TENANT_ID
    from app.models import Project

    project = Project(name="PRD Recovery Test", tenant_id=TEST_TENANT_ID)
    db.add(project)
    db.commit()
    db.refresh(project)

    transcript = Transcript(
        project_id=project.id,
        filename="prd-test.txt",
        content="Bob: We need a PRD",
        transcript_type="meeting",
        word_count=5,
        tenant_id=TEST_TENANT_ID,
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)

    extraction = Extraction(
        transcript_id=transcript.id,
        data_json=json.dumps({"decisions": []}),
        confidence=0.9,
        model_used="test-model",
        tenant_id=TEST_TENANT_ID,
    )
    db.add(extraction)
    db.commit()

    # Simulate a failed analysis after synthesis, with prd_requested flag
    synthesis_results = {
        "summary": {"totalTranscripts": 1},
        "conflicts": [],
        "prd_requested": True,
    }
    analysis = Analysis(
        project_id=project.id,
        status="recovering",
        last_checkpoint="synthesis_complete",
        results_json=json.dumps(synthesis_results),
        tenant_id=TEST_TENANT_ID,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    mock_prd.return_value = "# PRD\n\nGenerated PRD content"

    _resume_from_checkpoint(db, analysis, "synthesis_complete")

    assert analysis.status == "complete"
    assert analysis.last_checkpoint == "complete"
    mock_prd.assert_called_once()

    # Verify PRD is in results
    results = json.loads(analysis.results_json)
    assert "prd" in results
