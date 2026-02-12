"""Shared FastAPI dependencies."""

from fastapi import Request


def get_tenant_id(request: Request) -> str | None:
    """Extract tenant_id from request state (set by AuthMiddleware)."""
    return getattr(request.state, "tenant_id", None)
