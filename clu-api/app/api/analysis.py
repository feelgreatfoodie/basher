import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Analysis
from app.schemas import (
    AnalysisTriggerRequest,
    AnalysisResponse,
    AnalysisStatusResponse,
    AnalysisResultsResponse,
)
from app.services.pipeline import run_analysis_pipeline
from app.services.prd_generator import generate_prd as generate_prd_service

router = APIRouter(prefix="/projects/{project_id}", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse, status_code=202)
def trigger_analysis(
    project_id: str,
    background_tasks: BackgroundTasks,
    data: AnalysisTriggerRequest | None = None,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    analysis = Analysis(project_id=project_id, status="pending", tenant_id=project.tenant_id)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    background_tasks.add_task(run_analysis_pipeline, analysis.id, project_id)
    return analysis


@router.get("/analysis/status", response_model=AnalysisStatusResponse)
def get_analysis_status(project_id: str, db: Session = Depends(get_db)):
    analysis = (
        db.query(Analysis)
        .filter(Analysis.project_id == project_id)
        .order_by(Analysis.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this project")
    return analysis


@router.get("/analysis/results", response_model=AnalysisResultsResponse)
def get_analysis_results(project_id: str, db: Session = Depends(get_db)):
    analysis = (
        db.query(Analysis)
        .filter(Analysis.project_id == project_id)
        .order_by(Analysis.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this project")
    if analysis.status != "complete":
        raise HTTPException(status_code=409, detail=f"Analysis status is '{analysis.status}', not complete")
    return analysis


@router.get("/analysis/{result_type}")
def get_analysis_by_type(project_id: str, result_type: str, db: Session = Depends(get_db)):
    valid_types = [
        "summary", "conflicts", "gaps", "decisions",
        "requirements", "stakeholders", "action-items",
    ]
    if result_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid result type. Must be one of: {valid_types}")

    analysis = (
        db.query(Analysis)
        .filter(Analysis.project_id == project_id)
        .order_by(Analysis.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this project")
    if analysis.status != "complete":
        raise HTTPException(status_code=409, detail=f"Analysis status is '{analysis.status}', not complete")

    results = json.loads(analysis.results_json) if analysis.results_json else {}
    section = results.get(result_type)
    if section is None:
        raise HTTPException(status_code=404, detail=f"No '{result_type}' section in analysis results")

    return {"type": result_type, "data": section}


@router.post("/prd", status_code=202)
def generate_prd(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    analysis = (
        db.query(Analysis)
        .filter(Analysis.project_id == project_id, Analysis.status == "complete")
        .order_by(Analysis.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=409, detail="No completed analysis found. Run analysis first.")

    results = json.loads(analysis.results_json) if analysis.results_json else {}
    prd_markdown = generate_prd_service(results)
    return {"status": "complete", "prd": prd_markdown}
