from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.health import router as health_router
from app.logging_config import setup_logging
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.tenant import TenantMiddleware

# Configure structured logging before anything else
setup_logging(json_format=settings.log_json, level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="CLU API",
    description="Multi-transcript analysis and synthesis engine",
    version="0.4.0",
    lifespan=lifespan,
)

# Middleware stack (last added = outermost = first to execute in Starlette)
# Execution order: CORS → Auth → Tenant → RateLimit → Route handler
app.add_middleware(RateLimitMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health checks (no auth required — registered before API router)
app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_v1_prefix)
