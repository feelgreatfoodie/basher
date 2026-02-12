"""Rate limiting middleware using Redis sliding window."""

import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)

# Paths exempt from rate limiting
RATE_LIMIT_EXEMPT = {"/health", "/health/ready", "/docs", "/openapi.json", "/redoc"}


def _get_redis_client():
    """Lazy import to avoid circular dependencies and allow graceful degradation."""
    try:
        import redis
        return redis.from_url(settings.redis_url, decode_responses=True)
    except Exception as e:
        logger.warning("Redis unavailable for rate limiting: %s", e)
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in RATE_LIMIT_EXEMPT:
            return await call_next(request)

        # Get rate limit and key ID from auth middleware (set on request.state)
        api_key_id = getattr(request.state, "api_key_id", None)
        rate_limit = getattr(request.state, "rate_limit", 100)

        if not api_key_id:
            # No auth context — let auth middleware handle rejection
            return await call_next(request)

        # Check rate limit via Redis sliding window
        allowed, remaining, reset_at = self._check_rate_limit(
            api_key_id, rate_limit
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                    "Retry-After": str(max(1, reset_at - int(time.time()))),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)
        return response

    def _check_rate_limit(
        self, api_key_id: str, limit: int, window_seconds: int = 60
    ) -> tuple[bool, int, int]:
        """Sliding window rate limit check using Redis sorted sets.

        Returns (allowed, remaining, reset_timestamp).
        On Redis failure, allows the request (fail-open).
        """
        client = _get_redis_client()
        if not client:
            return True, limit, int(time.time()) + window_seconds

        now = time.time()
        window_start = now - window_seconds
        key = f"clu:ratelimit:{api_key_id}"

        try:
            pipe = client.pipeline()
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Count requests in current window
            pipe.zcard(key)
            # Add current request
            pipe.zadd(key, {f"{now}": now})
            # Set TTL on the key
            pipe.expire(key, window_seconds)
            results = pipe.execute()

            request_count = results[1]  # zcard result
            remaining = max(0, limit - request_count - 1)
            reset_at = int(now) + window_seconds

            if request_count >= limit:
                return False, 0, reset_at

            return True, remaining, reset_at
        except Exception as e:
            logger.warning("Rate limit check failed (allowing request): %s", e)
            return True, limit, int(time.time()) + window_seconds
