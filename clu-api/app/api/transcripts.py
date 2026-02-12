import re

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_tenant_id
from app.models import Project, Transcript
from app.schemas import TranscriptResponse, TranscriptList
from app.services.parsers import detect_and_parse

router = APIRouter(prefix="/projects/{project_id}/transcripts", tags=["transcripts"])

# Accepted file extensions
ACCEPTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def detect_transcript_type(content: str, filename: str) -> str:
    """Auto-detect transcript type from content and filename heuristics."""
    lower = content[:2000].lower()
    if re.search(r"^Q:|^A:|interviewer|interviewee", content[:2000], re.MULTILINE):
        return "interview"
    if re.search(r"^\w[\w\s]*:\s", content[:2000], re.MULTILINE):
        return "meeting"
    if re.search(r"\d{1,2}:\d{2}\s*(AM|PM|am|pm)?\s*\w+", content[:2000]):
        return "slack"
    if re.search(r"(^#{1,3}\s|\d+\.\d+\s|requirement|specification)", lower, re.MULTILINE):
        return "spec"
    return "other"


def _validate_extension(filename: str) -> None:
    """Validate that the file has an accepted extension."""
    lower = filename.lower()
    if not any(lower.endswith(ext) for ext in ACCEPTED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Accepted: {', '.join(sorted(ACCEPTED_EXTENSIONS))}",
        )


@router.post("", response_model=TranscriptResponse, status_code=201)
async def upload_transcript(
    project_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
    tenant_id: str | None = Depends(get_tenant_id),
):
    query = db.query(Project).filter(Project.id == project_id)
    if tenant_id:
        query = query.filter(Project.tenant_id == tenant_id)
    project = query.first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    filename = file.filename or "unknown.txt"
    _validate_extension(filename)

    raw_bytes = await file.read()

    try:
        content = detect_and_parse(filename, raw_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    word_count = len(content.split())
    transcript_type = detect_transcript_type(content, filename)

    transcript = Transcript(
        project_id=project_id,
        filename=filename,
        content=content,
        transcript_type=transcript_type,
        word_count=word_count,
        tenant_id=tenant_id,
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


@router.get("", response_model=TranscriptList)
def list_transcripts(
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

    transcripts = (
        db.query(Transcript)
        .filter(Transcript.project_id == project_id)
        .order_by(Transcript.created_at.desc())
        .all()
    )
    return TranscriptList(transcripts=transcripts, total=len(transcripts))
