from datetime import datetime

from pydantic import BaseModel


class TranscriptResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    transcript_type: str
    word_count: int
    tenant_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscriptList(BaseModel):
    transcripts: list[TranscriptResponse]
    total: int
