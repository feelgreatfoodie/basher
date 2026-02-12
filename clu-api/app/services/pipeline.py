"""Analysis pipeline — orchestrates extraction and synthesis as a background job."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def run_analysis_pipeline(analysis_id: str, project_id: str,
                          generate_prd_flag: bool = False) -> None:
    """Run the full extraction + synthesis pipeline for a project.

    Designed to be called from FastAPI BackgroundTasks.
    Creates its own DB session since background tasks outlive the request.
    """
    db: Session = SessionLocal()
    try:
        _execute_pipeline(db, analysis_id, project_id, generate_prd_flag)
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


def _extract_single(transcript_id: str, filename: str, content: str,
                     transcript_type: str, word_count: int,
                     tenant_id: str | None) -> dict:
    """Extract a single transcript. Runs in a thread pool worker.

    Returns dict with extraction result and metadata needed to persist it.
    Each worker uses its own DB-independent result dict — the caller persists.
    """
    result = extract_transcript(
        filename=filename,
        content=content,
        transcript_type=transcript_type,
        word_count=word_count,
    )
    return {
        "transcript_id": transcript_id,
        "filename": filename,
        "data": result["data"],
        "model_used": result["model_used"],
        "tenant_id": tenant_id,
    }


def _execute_pipeline(db: Session, analysis_id: str, project_id: str,
                       generate_prd_flag: bool = False) -> None:
    """Core pipeline logic with concurrent extraction."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise ValueError(f"Analysis {analysis_id} not found")

    analysis.status = "extracting"
    analysis.started_at = datetime.now(timezone.utc)
    db.commit()

    transcripts = (
        db.query(Transcript).filter(Transcript.project_id == project_id).all()
    )
    if not transcripts:
        raise ValueError(f"No transcripts found for project {project_id}")

    # Filter to only transcripts that haven't been extracted yet
    pending = []
    for t in transcripts:
        existing = (
            db.query(Extraction)
            .filter(Extraction.transcript_id == t.id)
            .first()
        )
        if existing:
            logger.info("Skipping %s (already extracted)", t.filename)
        else:
            pending.append(t)

    logger.info(
        "Extracting %d transcripts (%d already done, %d concurrent max)",
        len(pending), len(transcripts) - len(pending),
        settings.max_concurrent_extractions,
    )

    # Phase 1: Extract transcripts concurrently
    errors = []
    if pending:
        max_workers = min(settings.max_concurrent_extractions, len(pending))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(
                    _extract_single,
                    t.id, t.filename, t.content,
                    t.transcript_type, t.word_count, t.tenant_id,
                ): t.filename
                for t in pending
            }

            for future in as_completed(futures):
                filename = futures[future]
                try:
                    result = future.result()
                    confidence = score_extraction(result["data"])
                    extraction = Extraction(
                        transcript_id=result["transcript_id"],
                        data_json=json.dumps(result["data"]),
                        confidence=confidence,
                        model_used=result["model_used"],
                        tenant_id=result["tenant_id"],
                    )
                    db.add(extraction)
                    db.commit()
                    logger.info("Extracted %s (confidence=%.3f)", filename, confidence)
                except Exception as e:
                    logger.error("Extraction failed for %s: %s", filename, e)
                    errors.append(f"{filename}: {e}")

    if errors:
        error_summary = "; ".join(errors)
        raise RuntimeError(f"Extraction failed for {len(errors)} transcript(s): {error_summary}")

    analysis.last_checkpoint = "extraction_complete"
    db.commit()

    # Phase 1.5: Index extractions into ChromaDB for semantic search
    all_extractions = (
        db.query(Extraction)
        .join(Transcript)
        .filter(Transcript.project_id == project_id)
        .all()
    )

    extraction_data = [json.loads(e.data_json) for e in all_extractions]

    semantic_conflicts = []
    try:
        for ext_data in extraction_data:
            index_extraction(ext_data, project_id)
        semantic_conflicts = find_semantic_conflicts(project_id)
        logger.info("Found %d semantic conflict candidates for project %s",
                     len(semantic_conflicts), project_id)
    except Exception as e:
        logger.warning("ChromaDB indexing failed (non-fatal): %s", e)

    analysis.last_checkpoint = "indexing_complete"
    db.commit()

    # Phase 2: Synthesize all extractions
    analysis.status = "synthesizing"
    db.commit()

    synthesis = synthesize_extractions(extraction_data, semantic_conflicts=semantic_conflicts)

    analysis.last_checkpoint = "synthesis_complete"
    db.commit()

    # Optional Phase 3: Generate PRD
    if generate_prd_flag:
        logger.info("Generating PRD for analysis %s", analysis_id)
        synthesis["prd_requested"] = True
        prd_markdown = generate_prd(synthesis)
        synthesis["prd"] = prd_markdown
        analysis.last_checkpoint = "prd_complete"
        db.commit()

    analysis.last_checkpoint = "complete"
    analysis.status = "complete"
    analysis.results_json = json.dumps(synthesis)
    analysis.model_used = (
        f"extract:{all_extractions[0].model_used if all_extractions else 'unknown'},"
        f"synth:{settings.synthesis_model}"
    )
    analysis.completed_at = datetime.now(timezone.utc)
    db.commit()

    logger.info("Analysis %s complete", analysis_id)
