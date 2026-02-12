"""Redis caching layer for LLM responses and job status."""

import hashlib
import json
import logging

import redis

from app.config import settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    """Get or create Redis client (lazy singleton)."""
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def _content_hash(content: str) -> str:
    """Generate a stable hash for transcript content."""
    return hashlib.sha256(content.encode()).hexdigest()


def get_cached_extraction(content: str, model: str) -> dict | None:
    """Check if we have a cached extraction for this content + model.

    Returns the cached extraction data dict, or None if not cached.
    """
    try:
        client = _get_client()
        key = f"clu:extract:{model}:{_content_hash(content)}"
        cached = client.get(key)
        if cached:
            logger.info("Cache hit for extraction (hash=%s)", _content_hash(content)[:8])
            return json.loads(cached)
    except Exception as e:
        logger.warning("Redis cache lookup failed (non-fatal): %s", e)
    return None


def set_cached_extraction(content: str, model: str, extraction_data: dict, ttl: int = 86400) -> None:
    """Cache an extraction result. Default TTL: 24 hours."""
    try:
        client = _get_client()
        key = f"clu:extract:{model}:{_content_hash(content)}"
        client.setex(key, ttl, json.dumps(extraction_data))
        logger.info("Cached extraction (hash=%s, ttl=%ds)", _content_hash(content)[:8], ttl)
    except Exception as e:
        logger.warning("Redis cache write failed (non-fatal): %s", e)


def get_cached_synthesis(extractions_hash: str) -> dict | None:
    """Check if we have a cached synthesis for this set of extractions."""
    try:
        client = _get_client()
        key = f"clu:synth:{extractions_hash}"
        cached = client.get(key)
        if cached:
            logger.info("Cache hit for synthesis (hash=%s)", extractions_hash[:8])
            return json.loads(cached)
    except Exception as e:
        logger.warning("Redis cache lookup failed (non-fatal): %s", e)
    return None


def set_cached_synthesis(extractions_hash: str, synthesis_data: dict, ttl: int = 86400) -> None:
    """Cache a synthesis result. Default TTL: 24 hours."""
    try:
        client = _get_client()
        key = f"clu:synth:{extractions_hash}"
        client.setex(key, ttl, json.dumps(synthesis_data))
        logger.info("Cached synthesis (hash=%s, ttl=%ds)", extractions_hash[:8], ttl)
    except Exception as e:
        logger.warning("Redis cache write failed (non-fatal): %s", e)


def hash_extractions(extractions: list[dict]) -> str:
    """Generate a stable hash for a list of extraction dicts."""
    content = json.dumps(extractions, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def invalidate_project_cache(project_id: str) -> int:
    """Invalidate all cached data for a project. Returns number of keys deleted."""
    try:
        client = _get_client()
        keys = list(client.scan_iter(f"clu:*:{project_id}:*"))
        if keys:
            return client.delete(*keys)
    except Exception as e:
        logger.warning("Redis cache invalidation failed (non-fatal): %s", e)
    return 0
