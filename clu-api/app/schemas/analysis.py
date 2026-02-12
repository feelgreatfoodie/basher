from datetime import datetime

from pydantic import BaseModel


class AnalysisTriggerRequest(BaseModel):
    generate_prd: bool = False


class AnalysisResponse(BaseModel):
    id: str
    project_id: str
    status: str
    error_message: str | None
    model_used: str | None
    tenant_id: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisStatusResponse(BaseModel):
    id: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None


class AnalysisResultsResponse(BaseModel):
    id: str
    project_id: str
    status: str
    results_json: str | None
    completed_at: datetime | None
