import json
from unittest.mock import patch

from app.database import Base
from app.models import Project, Transcript, Analysis, Extraction
from tests.conftest import engine, TestingSessionLocal


def _setup_db():
    """Create tables and return a fresh session."""
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def _teardown_db():
    Base.metadata.drop_all(bind=engine)


def _create_project_with_transcripts(db, count=2):
    """Helper: create a project with N transcripts."""
    project = Project(name="Test Project")
    db.add(project)
    db.commit()
    db.refresh(project)

    for i in range(count):
        t = Transcript(
            project_id=project.id,
            filename=f"meeting-{i}.txt",
            content=f"Alice: Point {i}.\nBob: Agreed on {i}.",
            transcript_type="meeting",
            word_count=6,
        )
        db.add(t)
    db.commit()

    analysis = Analysis(project_id=project.id, status="pending")
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return project, analysis


MOCK_EXTRACTION = {
    "source": {"name": "test.txt", "type": "meeting", "wordCount": 6},
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
    "summary": {"totalTranscripts": 2, "conflictsFound": 0, "gapsFound": 0, "highlights": []},
    "conflicts": [],
    "gaps": [],
    "decisions": [],
    "requirements": [],
    "stakeholders": [],
    "actionItems": [],
}


@patch("app.services.pipeline.find_semantic_conflicts", return_value=[])
@patch("app.services.pipeline.index_extraction")
@patch("app.services.pipeline.score_extraction", return_value=0.85)
@patch("app.services.pipeline.synthesize_extractions")
@patch("app.services.pipeline.extract_transcript")
@patch("app.services.pipeline.SessionLocal", side_effect=lambda: TestingSessionLocal())
def test_pipeline_runs_to_completion(mock_session_cls, mock_extract, mock_synth,
                                     mock_score, mock_index, mock_conflicts):
    db = _setup_db()
    try:
        mock_extract.return_value = {"data": MOCK_EXTRACTION, "model_used": "test-model"}
        mock_synth.return_value = MOCK_SYNTHESIS

        project, analysis = _create_project_with_transcripts(db, count=2)
        analysis_id = analysis.id
        project_id = project.id
        db.close()

        from app.services.pipeline import run_analysis_pipeline
        run_analysis_pipeline(analysis_id, project_id)

        check = TestingSessionLocal()
        updated = check.query(Analysis).filter(Analysis.id == analysis_id).first()
        assert updated.status == "complete"
        assert updated.results_json is not None
        assert updated.completed_at is not None
        assert mock_extract.call_count == 2
        mock_synth.assert_called_once()
        check.close()
    finally:
        _teardown_db()


@patch("app.services.pipeline.find_semantic_conflicts", return_value=[])
@patch("app.services.pipeline.index_extraction")
@patch("app.services.pipeline.score_extraction", return_value=0.85)
@patch("app.services.pipeline.synthesize_extractions")
@patch("app.services.pipeline.extract_transcript")
@patch("app.services.pipeline.SessionLocal", side_effect=lambda: TestingSessionLocal())
def test_pipeline_skips_already_extracted(mock_session_cls, mock_extract, mock_synth,
                                          mock_score, mock_index, mock_conflicts):
    db = _setup_db()
    try:
        mock_extract.return_value = {"data": MOCK_EXTRACTION, "model_used": "test-model"}
        mock_synth.return_value = MOCK_SYNTHESIS

        project, analysis = _create_project_with_transcripts(db, count=2)
        analysis_id = analysis.id
        project_id = project.id

        # Pre-extract one transcript
        transcripts = db.query(Transcript).filter(Transcript.project_id == project_id).all()
        ext = Extraction(
            transcript_id=transcripts[0].id,
            data_json=json.dumps(MOCK_EXTRACTION),
            model_used="pre-existing",
        )
        db.add(ext)
        db.commit()
        db.close()

        from app.services.pipeline import run_analysis_pipeline
        run_analysis_pipeline(analysis_id, project_id)

        check = TestingSessionLocal()
        updated = check.query(Analysis).filter(Analysis.id == analysis_id).first()
        assert updated.status == "complete"
        assert mock_extract.call_count == 1
        check.close()
    finally:
        _teardown_db()


@patch("app.services.pipeline.find_semantic_conflicts", return_value=[])
@patch("app.services.pipeline.index_extraction")
@patch("app.services.pipeline.score_extraction", return_value=0.85)
@patch("app.services.pipeline.synthesize_extractions")
@patch("app.services.pipeline.extract_transcript")
@patch("app.services.pipeline.SessionLocal", side_effect=lambda: TestingSessionLocal())
def test_pipeline_handles_extraction_failure(mock_session_cls, mock_extract, mock_synth,
                                              mock_score, mock_index, mock_conflicts):
    db = _setup_db()
    try:
        mock_extract.side_effect = RuntimeError("API error")

        project, analysis = _create_project_with_transcripts(db, count=1)
        analysis_id = analysis.id
        project_id = project.id
        db.close()

        from app.services.pipeline import run_analysis_pipeline
        run_analysis_pipeline(analysis_id, project_id)

        check = TestingSessionLocal()
        updated = check.query(Analysis).filter(Analysis.id == analysis_id).first()
        assert updated.status == "failed"
        assert "API error" in updated.error_message
        check.close()
    finally:
        _teardown_db()


@patch("app.services.pipeline.find_semantic_conflicts", return_value=[])
@patch("app.services.pipeline.index_extraction")
@patch("app.services.pipeline.score_extraction", return_value=0.85)
@patch("app.services.pipeline.generate_prd")
@patch("app.services.pipeline.synthesize_extractions")
@patch("app.services.pipeline.extract_transcript")
@patch("app.services.pipeline.SessionLocal", side_effect=lambda: TestingSessionLocal())
def test_pipeline_generates_prd_when_requested(mock_session_cls, mock_extract, mock_synth, mock_prd,
                                                mock_score, mock_index, mock_conflicts):
    db = _setup_db()
    try:
        mock_extract.return_value = {"data": MOCK_EXTRACTION, "model_used": "test-model"}
        mock_synth.return_value = MOCK_SYNTHESIS.copy()
        mock_prd.return_value = "# PRD\n\n## Stories\n..."

        project, analysis = _create_project_with_transcripts(db, count=1)
        analysis_id = analysis.id
        project_id = project.id
        db.close()

        from app.services.pipeline import run_analysis_pipeline
        run_analysis_pipeline(analysis_id, project_id, generate_prd_flag=True)

        check = TestingSessionLocal()
        updated = check.query(Analysis).filter(Analysis.id == analysis_id).first()
        assert updated.status == "complete"
        results = json.loads(updated.results_json)
        assert "prd" in results
        mock_prd.assert_called_once()
        check.close()
    finally:
        _teardown_db()
