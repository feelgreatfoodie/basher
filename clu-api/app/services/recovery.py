"""Job recovery — resume failed analyses from last checkpoint."""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Analysis, Transcript, Extraction
from app.services.confidence import score_extraction
from app.services.embeddings import index_extraction, find_semantic_conflicts
from app.services.extractor import extract_transcript
from app.services.prd_generator import generate_prd
from app.services.synthesizer import synthesize_extractions

logger = logging.getLogger(__name__)

# Checkpoint names (in pipeline order)
CHECKPOINTS = [
    "extraction_complete",
    "indexing_complete",
    "synthesis_complete",
    "prd_complete",
    "complete",
]


def recover_analysis(analysis_id: str) -> None:
    """Resume a failed analysis from its last checkpoint.

    Designed to be called from FastAPI BackgroundTasks.
    Creates its own DB session since background tasks outlive the request.
    """
    db: Session = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        if analysis.status != "failed":
            raise ValueError(
                f"Analysis {analysis_id} status is '{analysis.status}', not 'failed'"
            )

        checkpoint = analysis.last_checkpoint
        logger.info(
            "Recovering analysis %s from checkpoint '%s'",
            analysis_id, checkpoint or "none",
        )

        # Reset status
        analysis.status = "recovering"
        analysis.error_message = None
        db.commit()

        _resume_from_checkpoint(db, analysis, checkpoint)

    except Exception as e:
        logger.exception("Recovery failed for analysis %s", analysis_id)
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = "failed"
            analysis.error_message = f"Recovery failed: {e}"
            analysis.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def _resume_from_checkpoint(
    db: Session, analysis: Analysis, checkpoint: str | None
) -> None:
    """Resume pipeline execution from the given checkpoint."""
    project_id = analysis.project_id

    transcripts = (
        db.query(Transcript).filter(Transcript.project_id == project_id).all()
    )
    if not transcripts:
        raise ValueError(f"No transcripts found for project {project_id}")

    # Determine where to resume based on last completed checkpoint
    if checkpoint is None or checkpoint == "extraction_complete":
        # Need to complete extraction phase (or start from scratch)
        if checkpoint is None:
            _run_extraction(db, analysis, transcripts)

    if checkpoint in (None, "extraction_complete"):
        # Need to run indexing + synthesis
        _run_indexing_and_synthesis(db, analysis, project_id)

    # Check if PRD was requested (look at existing partial results)
    existing_results = json.loads(analysis.results_json) if analysis.results_json else {}
    generate_prd_flag = "prd_requested" in existing_results

    if generate_prd_flag and checkpoint in (
        None, "extraction_complete", "indexing_complete", "synthesis_complete",
    ):
        _run_prd_generation(db, analysis)

    # Mark complete
    analysis.status = "complete"
    analysis.last_checkpoint = "complete"
    analysis.completed_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("Recovery complete for analysis %s", analysis.id)


def _run_extraction(
    db: Session, analysis: Analysis, transcripts: list[Transcript]
) -> None:
    """Run extraction for any transcripts not yet extracted."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    analysis.status = "extracting"
    db.commit()

    pending = []
    for t in transcripts:
        existing = (
            db.query(Extraction)
            .filter(Extraction.transcript_id == t.id)
            .first()
        )
        if not existing:
            pending.append(t)

    if not pending:
        logger.info("All transcripts already extracted, skipping extraction phase")
        analysis.last_checkpoint = "extraction"
        db.commit()
        return

    logger.info("Extracting %d remaining transcripts", len(pending))
    errors = []
    max_workers = min(settings.max_concurrent_extractions, len(pending))

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                extract_transcript,
                filename=t.filename,
                content=t.content,
                transcript_type=t.transcript_type,
                word_count=t.word_count,
            ): t
            for t in pending
        }

        for future in as_completed(futures):
            transcript = futures[future]
            try:
                result = future.result()
                confidence = score_extraction(result["data"])
                extraction = Extraction(
                    transcript_id=transcript.id,
                    data_json=json.dumps(result["data"]),
                    confidence=confidence,
                    model_used=result["model_used"],
                    tenant_id=transcript.tenant_id,
                )
                db.add(extraction)
                db.commit()
                logger.info(
                    "Recovered extraction for %s (confidence=%.3f)",
                    transcript.filename, confidence,
                )
            except Exception as e:
                logger.error(
                    "Extraction failed for %s during recovery: %s",
                    transcript.filename, e,
                )
                errors.append(f"{transcript.filename}: {e}")

    if errors:
        raise RuntimeError(
            f"Extraction failed for {len(errors)} transcript(s): {'; '.join(errors)}"
        )

    analysis.last_checkpoint = "extraction_complete"
    db.commit()


def _run_indexing_and_synthesis(
    db: Session, analysis: Analysis, project_id: str
) -> None:
    """Run ChromaDB indexing and synthesis."""
    all_extractions = (
        db.query(Extraction)
        .join(Transcript)
        .filter(Transcript.project_id == project_id)
        .all()
    )
    extraction_data = [json.loads(e.data_json) for e in all_extractions]

    # Phase: Indexing
    semantic_conflicts = []
    try:
        for ext_data in extraction_data:
            index_extraction(ext_data, project_id)
        semantic_conflicts = find_semantic_conflicts(project_id)
        logger.info(
            "Found %d semantic conflicts during recovery", len(semantic_conflicts)
        )
    except Exception as e:
        logger.warning("ChromaDB indexing failed during recovery (non-fatal): %s", e)

    analysis.last_checkpoint = "indexing_complete"
    db.commit()

    # Phase: Synthesis
    analysis.status = "synthesizing"
    db.commit()

    synthesis = synthesize_extractions(
        extraction_data, semantic_conflicts=semantic_conflicts
    )

    analysis.results_json = json.dumps(synthesis)
    analysis.last_checkpoint = "synthesis"
    analysis.model_used = (
        f"extract:{all_extractions[0].model_used if all_extractions else 'unknown'},"
        f"synth:{settings.synthesis_model}"
    )
    db.commit()


def _run_prd_generation(db: Session, analysis: Analysis) -> None:
    """Generate PRD from existing synthesis results."""
    logger.info("Generating PRD during recovery for analysis %s", analysis.id)
    results = json.loads(analysis.results_json) if analysis.results_json else {}
    prd_markdown = generate_prd(results)
    results["prd"] = prd_markdown
    analysis.results_json = json.dumps(results)
    analysis.last_checkpoint = "prd"
    db.commit()
