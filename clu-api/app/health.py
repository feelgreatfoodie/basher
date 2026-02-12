"""Health check endpoints for CLU API."""

import logging

from fastapi import APIRouter

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Basic liveness check."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness():
    """Readiness check — verifies database and service dependencies."""
    checks = {}

    # Check database
    checks["database"] = _check_database()

    # Check Redis
    checks["redis"] = _check_redis()

    # Check ChromaDB
    checks["chromadb"] = _check_chromadb()

    overall = "ok" if all(c["status"] == "ok" for c in checks.values()) else "degraded"

    return {"status": overall, "checks": checks}


def _check_database() -> dict:
    """Verify database connectivity."""
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            return {"status": "ok"}
        finally:
            db.close()
    except Exception as e:
        logger.warning("Database health check failed: %s", e)
        return {"status": "error", "detail": str(e)}


def _check_redis() -> dict:
    """Verify Redis connectivity."""
    try:
        import redis
        client = redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        return {"status": "ok"}
    except Exception as e:
        logger.warning("Redis health check failed: %s", e)
        return {"status": "error", "detail": str(e)}


def _check_chromadb() -> dict:
    """Verify ChromaDB connectivity."""
    try:
        import chromadb
        client = chromadb.HttpClient(
            host=settings.chromadb_host, port=settings.chromadb_port
        )
        client.heartbeat()
        return {"status": "ok"}
    except Exception as e:
        logger.warning("ChromaDB health check failed: %s", e)
        return {"status": "error", "detail": str(e)}
