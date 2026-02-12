import re

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Transcript
from app.schemas import TranscriptResponse, TranscriptList

router = APIRouter(prefix="/projects/{project_id}/transcripts", tags=["transcripts"])


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


@router.post("", response_model=TranscriptResponse, status_code=201)
async def upload_transcript(
    project_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = (await file.read()).decode("utf-8")
    word_count = len(content.split())
    transcript_type = detect_transcript_type(content, file.filename or "unknown.txt")

    transcript = Transcript(
        project_id=project_id,
        filename=file.filename or "unknown.txt",
        content=content,
        transcript_type=transcript_type,
        word_count=word_count,
        tenant_id=project.tenant_id,
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


@router.get("", response_model=TranscriptList)
def list_transcripts(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    transcripts = (
        db.query(Transcript)
        .filter(Transcript.project_id == project_id)
        .order_by(Transcript.created_at.desc())
        .all()
    )
    return TranscriptList(transcripts=transcripts, total=len(transcripts))
