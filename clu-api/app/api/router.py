from fastapi import APIRouter

from app.api.projects import router as projects_router
from app.api.transcripts import router as transcripts_router
from app.api.analysis import router as analysis_router, templates_router

api_router = APIRouter()
api_router.include_router(projects_router)
api_router.include_router(transcripts_router)
api_router.include_router(analysis_router)
api_router.include_router(templates_router)
