"""Tenant isolation middleware.

Extracts tenant_id from request state (set by auth middleware)
and makes it available for downstream route handlers.
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Paths that don't need tenant context
TENANT_EXEMPT = {"/health", "/docs", "/openapi.json", "/redoc"}


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in TENANT_EXEMPT:
            return await call_next(request)

        # tenant_id is set by AuthMiddleware from the API key record
        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            logger.debug("Request scoped to tenant: %s", tenant_id)

        return await call_next(request)
