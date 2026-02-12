"""API key authentication middleware.

Extracts API key from Authorization: Bearer header, validates against DB,
and injects tenant_id into request state for downstream use.
"""

import hashlib
from datetime import datetime, timezone

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import SessionLocal
from app.models.api_key import ApiKey

# Paths that don't require authentication
PUBLIC_PATHS = {"/health", "/health/ready", "/docs", "/openapi.json", "/redoc"}


def _hash_key(key: str) -> str:
    """Hash an API key for comparison with stored hash."""
    return hashlib.sha256(key.encode()).hexdigest()


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Extract bearer token
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        api_key = auth_header[7:]  # Strip "Bearer "
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing API key"},
            )

        # Validate key against DB
        key_hash = _hash_key(api_key)
        db = SessionLocal()
        try:
            api_key_record = (
                db.query(ApiKey)
                .filter(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
                .first()
            )

            if not api_key_record:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid or inactive API key"},
                )

            # Update last_used timestamp
            api_key_record.last_used_at = datetime.now(timezone.utc)
            db.commit()

            # Inject tenant context into request state
            request.state.tenant_id = api_key_record.tenant_id
            request.state.api_key_id = api_key_record.id
            request.state.rate_limit = api_key_record.rate_limit
        finally:
            db.close()

        return await call_next(request)
