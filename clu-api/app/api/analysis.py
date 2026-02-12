import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_tenant_id
from app.models import Project, Analysis, Transcript, Extraction
from app.schemas import (
    AnalysisTriggerRequest,
    AnalysisResponse,
    AnalysisStatusResponse,
    AnalysisResultsResponse,
)
from app.services.pipeline import run_analysis_pipeline
from app.services.prd_generator import generate_prd as generate_prd_service
from app.services.recovery import recover_analysis

router = APIRouter(prefix="/projects/{project_id}", tags=["analysis"])


def _get_project(db: Session, project_id: str, tenant_id: str | None) -> Project:
    """Look up a project scoped by tenant. Raises 404 if not found."""
    query = db.query(Project).filter(Project.id == project_id)
    if tenant_id:
        query = query.filter(Project.tenant_id == tenant_id)
    project = query.first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_latest_analysis(
    db: Session, project_id: str, tenant_id: str | None, status: str | None = None
) -> Analysis:
    """Look up the latest analysis for a project, scoped by tenant."""
    query = db.query(Analysis).filter(Analysis.project_id == project_id)
    if tenant_id:
        query = query.filter(Analysis.tenant_id == tenant_id)
    if status:
        query = query.filter(Analysis.status == status)
    analysis = query.order_by(Analysis.created_at.desc()).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this project")
    return analysis


@router.post("/analyze", response_model=AnalysisResponse, status_code=202)
def trigger_analysis(
    project_id: str,
    background_tasks: BackgroundTasks,
    data: AnalysisTriggerRequest | None = None,
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_tenant_id),
):
    project = _get_project(db, project_id, tenant_id)

    analysis = Analysis(project_id=project_id, status="pending", tenant_id=tenant_id)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    generate_prd_flag = data.generate_prd if data else False
    background_tasks.add_task(
        run_analysis_pipeline, analysis.id, project_id, generate_prd_flag
    )
    return analysis


@router.get("/analysis/status", response_model=AnalysisStatusResponse)
def get_analysis_status(
    project_id: str,
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_tenant_id),
):
    analysis = _get_latest_analysis(db, project_id, tenant_id)
    return analysis


@router.get("/analysis/results", response_model=AnalysisResultsResponse)
def get_analysis_results(
    project_id: str,
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_tenant_id),
):
    analysis = _get_latest_analysis(db, project_id, tenant_id)
    if analysis.status != "complete":
        raise HTTPException(
            status_code=409,
            detail=f"Analysis status is '{analysis.status}', not complete",
        )
    return analysis


@router.get("/analysis/confidence")
def get_extraction_confidence(
    project_id: str,
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_tenant_id),
):
    """Get confidence scores for all extractions in a project."""
    _get_project(db, project_id, tenant_id)

    query = (
        db.query(Extraction, Transcript.filename)
        .join(Transcript)
        .filter(Transcript.project_id == project_id)
    )
    if tenant_id:
        query = query.filter(Extraction.tenant_id == tenant_id)
    extractions = query.all()

    if not extractions:
        raise HTTPException(status_code=404, detail="No extractions found for this project")

    scores = [
        {
            "transcript_id": ext.transcript_id,
            "filename": filename,
            "confidence": ext.confidence,
        }
        for ext, filename in extractions
    ]

    avg_confidence = (
        sum(s["confidence"] for s in scores if s["confidence"] is not None)
        / max(sum(1 for s in scores if s["confidence"] is not None), 1)
    )

    return {
        "project_id": project_id,
        "average_confidence": round(avg_confidence, 3),
        "extractions": scores,
    }


@router.get("/analysis/{result_type}")
def get_analysis_by_type(
    project_id: str,
    result_type: str,
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_tenant_id),
):
    valid_types = [
        "summary", "conflicts", "gaps", "decisions",
        "requirements", "stakeholders", "action-items",
    ]
    if result_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid result type. Must be one of: {valid_types}",
        )

    analysis = _get_latest_analysis(db, project_id, tenant_id)
    if analysis.status != "complete":
        raise HTTPException(
            status_code=409,
            detail=f"Analysis status is '{analysis.status}', not complete",
        )

    results = json.loads(analysis.results_json) if analysis.results_json else {}
    section = results.get(result_type)
    if section is None:
        raise HTTPException(
            status_code=404, detail=f"No '{result_type}' section in analysis results"
        )

    return {"type": result_type, "data": section}


@router.post("/analysis/retry", status_code=202)
def retry_failed_analysis(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_tenant_id),
):
    """Retry the latest failed analysis, resuming from its last checkpoint."""
    _get_project(db, project_id, tenant_id)

    analysis = _get_latest_analysis(db, project_id, tenant_id)
    if analysis.status != "failed":
        raise HTTPException(
            status_code=409,
            detail=f"Latest analysis status is '{analysis.status}', not 'failed'",
        )

    if not analysis.last_checkpoint:
        raise HTTPException(
            status_code=409,
            detail="Analysis has no checkpoint to resume from. Trigger a new analysis instead.",
        )

    background_tasks.add_task(recover_analysis, analysis.id)
    return {
        "id": analysis.id,
        "status": "recovering",
        "last_checkpoint": analysis.last_checkpoint,
        "message": f"Resuming from checkpoint '{analysis.last_checkpoint}'",
    }


@router.post("/prd", status_code=202)
def generate_prd(
    project_id: str,
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_tenant_id),
):
    _get_project(db, project_id, tenant_id)

    analysis = _get_latest_analysis(db, project_id, tenant_id, status="complete")

    results = json.loads(analysis.results_json) if analysis.results_json else {}
    prd_markdown = generate_prd_service(results)
    return {"status": "complete", "prd": prd_markdown}
