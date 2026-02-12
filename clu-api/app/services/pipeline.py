"""Analysis pipeline — orchestrates extraction and synthesis as a background job."""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Analysis, Transcript, Extraction
from app.services.extractor import extract_transcript
from app.services.synthesizer import synthesize_extractions

logger = logging.getLogger(__name__)


def run_analysis_pipeline(analysis_id: str, project_id: str) -> None:
    """Run the full extraction + synthesis pipeline for a project.

    Designed to be called from FastAPI BackgroundTasks.
    Creates its own DB session since background tasks outlive the request.
    """
    db: Session = SessionLocal()
    try:
        _execute_pipeline(db, analysis_id, project_id)
    except Exception as e:
        logger.exception("Analysis pipeline failed for %s", analysis_id)
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def _execute_pipeline(db: Session, analysis_id: str, project_id: str) -> None:
    """Core pipeline logic."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise ValueError(f"Analysis {analysis_id} not found")

    # Mark as extracting
    analysis.status = "extracting"
    analysis.started_at = datetime.now(timezone.utc)
    db.commit()

    # Get all transcripts for this project
    transcripts = (
        db.query(Transcript).filter(Transcript.project_id == project_id).all()
    )
    if not transcripts:
        raise ValueError(f"No transcripts found for project {project_id}")

    logger.info("Starting extraction for %d transcripts", len(transcripts))

    # Phase 1: Extract each transcript
    for transcript in transcripts:
        # Skip if already extracted
        existing = (
            db.query(Extraction)
            .filter(Extraction.transcript_id == transcript.id)
            .first()
        )
        if existing:
            logger.info("Skipping %s (already extracted)", transcript.filename)
            continue

        result = extract_transcript(
            filename=transcript.filename,
            content=transcript.content,
            transcript_type=transcript.transcript_type,
            word_count=transcript.word_count,
        )

        extraction = Extraction(
            transcript_id=transcript.id,
            data_json=json.dumps(result["data"]),
            model_used=result["model_used"],
            tenant_id=transcript.tenant_id,
        )
        db.add(extraction)
        db.commit()
        logger.info("Extracted %s", transcript.filename)

    # Phase 2: Synthesize all extractions
    analysis.status = "synthesizing"
    db.commit()

    all_extractions = (
        db.query(Extraction)
        .join(Transcript)
        .filter(Transcript.project_id == project_id)
        .all()
    )

    extraction_data = [json.loads(e.data_json) for e in all_extractions]
    synthesis = synthesize_extractions(extraction_data)

    # Save results
    analysis.status = "complete"
    analysis.results_json = json.dumps(synthesis)
    analysis.model_used = f"extract:{all_extractions[0].model_used if all_extractions else 'unknown'},synth:{analysis.model_used or 'opus'}"
    analysis.completed_at = datetime.now(timezone.utc)
    db.commit()

    logger.info("Analysis %s complete", analysis_id)
