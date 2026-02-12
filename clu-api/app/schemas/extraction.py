from datetime import datetime

from pydantic import BaseModel


class ExtractionResponse(BaseModel):
    id: str
    transcript_id: str
    data_json: str
    confidence: float | None
    model_used: str
    tenant_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
