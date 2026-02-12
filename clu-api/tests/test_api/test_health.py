"""Tests for health check endpoints."""

from unittest.mock import patch


def test_health_liveness(unauthed_client):
    """Basic health check should return ok without auth."""
    response = unauthed_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_readiness(unauthed_client):
    """Readiness check should return status for each dependency."""
    response = unauthed_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]
    assert "chromadb" in data["checks"]


@patch("app.health._check_database")
@patch("app.health._check_redis")
@patch("app.health._check_chromadb")
def test_health_readiness_all_ok(mock_chromadb, mock_redis, mock_db, unauthed_client):
    """When all checks pass, overall status should be ok."""
    mock_db.return_value = {"status": "ok"}
    mock_redis.return_value = {"status": "ok"}
    mock_chromadb.return_value = {"status": "ok"}

    response = unauthed_client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("app.health._check_database")
@patch("app.health._check_redis")
@patch("app.health._check_chromadb")
def test_health_readiness_degraded(mock_chromadb, mock_redis, mock_db, unauthed_client):
    """When any check fails, overall status should be degraded."""
    mock_db.return_value = {"status": "ok"}
    mock_redis.return_value = {"status": "error", "detail": "Connection refused"}
    mock_chromadb.return_value = {"status": "ok"}

    response = unauthed_client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
