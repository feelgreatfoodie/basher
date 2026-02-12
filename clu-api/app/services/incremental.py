"""Incremental analysis — add new transcripts without re-running everything."""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Analysis, Transcript, Extraction
from app.services.confidence import score_extraction
from app.services.embeddings import index_extraction, find_semantic_conflicts
from app.services.extractor import extract_transcript
from app.services.prd_generator import generate_prd
from app.services.synthesizer import synthesize_extractions

logger = logging.getLogger(__name__)


def run_incremental_analysis(
    analysis_id: str,
    project_id: str,
    generate_prd_flag: bool = False,
) -> None:
    """Run incremental extraction + synthesis for new transcripts only.

    Finds transcripts that don't have extractions yet, extracts them,
    then re-synthesizes by merging new extractions with existing ones.
    """
    from app.database import SessionLocal

    db: Session = SessionLocal()
    try:
        _execute_incremental(db, analysis_id, project_id, generate_prd_flag)
    except Exception as e:
        logger.exception("Incremental pipeline failed for %s", analysis_id)
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def _execute_incremental(
    db: Session,
    analysis_id: str,
    project_id: str,
    generate_prd_flag: bool = False,
) -> None:
    """Core incremental logic: extract only new transcripts, re-synthesize all."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise ValueError(f"Analysis {analysis_id} not found")

    analysis.status = "extracting"
    analysis.started_at = datetime.now(timezone.utc)
    db.commit()

    # Get all transcripts for the project
    transcripts = (
        db.query(Transcript).filter(Transcript.project_id == project_id).all()
    )
    if not transcripts:
        raise ValueError(f"No transcripts found for project {project_id}")

    # Find transcripts that don't have extractions yet
    new_transcripts = []
    existing_count = 0
    for t in transcripts:
        existing = (
            db.query(Extraction).filter(Extraction.transcript_id == t.id).first()
        )
        if existing:
            existing_count += 1
        else:
            new_transcripts.append(t)

    if not new_transcripts:
        raise ValueError("No new transcripts to extract. All transcripts already have extractions.")

    logger.info(
        "Incremental: %d new transcripts to extract, %d already done",
        len(new_transcripts), existing_count,
    )

    analysis.last_checkpoint = "incremental_extraction_start"
    db.commit()

    # Extract only new transcripts
    errors = []
    max_workers = min(settings.max_concurrent_extractions, len(new_transcripts))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                extract_transcript,
                filename=t.filename,
                content=t.content,
                transcript_type=t.transcript_type,
                word_count=t.word_count,
            ): t
            for t in new_transcripts
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
                    "Incremental extracted %s (confidence=%.3f)",
                    transcript.filename, confidence,
                )
            except Exception as e:
                logger.error(
                    "Incremental extraction failed for %s: %s",
                    transcript.filename, e,
                )
                errors.append(f"{transcript.filename}: {e}")

    if errors:
        error_summary = "; ".join(errors)
        raise RuntimeError(
            f"Incremental extraction failed for {len(errors)} transcript(s): {error_summary}"
        )

    analysis.last_checkpoint = "incremental_extraction_complete"
    db.commit()

    # Index new extractions into ChromaDB
    all_extractions = (
        db.query(Extraction)
        .join(Transcript)
        .filter(Transcript.project_id == project_id)
        .all()
    )
    extraction_data = [json.loads(e.data_json) for e in all_extractions]

    semantic_conflicts = []
    try:
        for ext in all_extractions:
            index_extraction(json.loads(ext.data_json), project_id)
        semantic_conflicts = find_semantic_conflicts(project_id)
        logger.info(
            "Found %d semantic conflict candidates",
            len(semantic_conflicts),
        )
    except Exception as e:
        logger.warning("ChromaDB indexing failed (non-fatal): %s", e)

    analysis.last_checkpoint = "incremental_indexing_complete"
    db.commit()

    # Re-synthesize all extractions (new + existing)
    analysis.status = "synthesizing"
    db.commit()

    synthesis = synthesize_extractions(extraction_data, semantic_conflicts=semantic_conflicts)

    analysis.last_checkpoint = "incremental_synthesis_complete"
    db.commit()

    # Optional: Generate PRD
    if generate_prd_flag:
        logger.info("Generating PRD for incremental analysis %s", analysis_id)
        synthesis["prd_requested"] = True
        prd_markdown = generate_prd(synthesis)
        synthesis["prd"] = prd_markdown
        analysis.last_checkpoint = "incremental_prd_complete"
        db.commit()

    analysis.status = "complete"
    analysis.results_json = json.dumps(synthesis)
    analysis.model_used = (
        f"incremental:extract:{all_extractions[0].model_used if all_extractions else 'unknown'},"
        f"synth:{settings.synthesis_model}"
    )
    analysis.completed_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "Incremental analysis %s complete: %d new + %d existing = %d total extractions",
        analysis_id, len(new_transcripts), existing_count, len(all_extractions),
    )
