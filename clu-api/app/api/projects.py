from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_tenant_id
from app.models import Project
from app.schemas import ProjectCreate, ProjectResponse, ProjectList

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_tenant_id),
):
    project = Project(name=data.name, description=data.description, tenant_id=tenant_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=ProjectList)
def list_projects(
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_tenant_id),
):
    query = db.query(Project)
    if tenant_id:
        query = query.filter(Project.tenant_id == tenant_id)
    projects = query.order_by(Project.created_at.desc()).all()
    return ProjectList(projects=projects, total=len(projects))


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_tenant_id),
):
    query = db.query(Project).filter(Project.id == project_id)
    if tenant_id:
        query = query.filter(Project.tenant_id == tenant_id)
    project = query.first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
