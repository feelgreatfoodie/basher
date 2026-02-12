"""Tests for rate limiting middleware."""

from unittest.mock import patch, MagicMock


def test_rate_limit_headers_present(client):
    """Authenticated requests should include rate limit headers."""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_rate_limit_allows_under_limit(client):
    """Requests under the limit should succeed."""
    for _ in range(5):
        response = client.get("/api/v1/projects")
        assert response.status_code == 200


@patch("app.middleware.rate_limit._get_redis_client")
def test_rate_limit_exceeded(mock_redis_client, client):
    """Requests over the limit should get 429."""
    mock_client = MagicMock()
    mock_redis_client.return_value = mock_client

    # Simulate rate limit exceeded: zcard returns count >= limit
    mock_pipe = MagicMock()
    mock_pipe.execute.return_value = [
        None,   # zremrangebyscore result
        200,    # zcard result (over the 100 limit)
        None,   # zadd result
        None,   # expire result
    ]
    mock_client.pipeline.return_value = mock_pipe

    response = client.get("/api/v1/projects")
    assert response.status_code == 429
    assert "Rate limit" in response.json()["detail"]
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert "Retry-After" in response.headers


@patch("app.middleware.rate_limit._get_redis_client")
def test_rate_limit_redis_failure_allows_request(mock_redis_client, client):
    """When Redis is down, requests should still be allowed (fail-open)."""
    mock_redis_client.return_value = None

    response = client.get("/api/v1/projects")
    assert response.status_code == 200


def test_health_exempt_from_rate_limit(unauthed_client):
    """Health endpoint should not be rate limited."""
    response = unauthed_client.get("/health")
    assert response.status_code == 200
    assert "X-RateLimit-Limit" not in response.headers
