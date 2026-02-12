"""Tests for API key authentication middleware."""

from tests.conftest import TEST_API_KEY


def test_health_no_auth_required(unauthed_client):
    """Health endpoint should be accessible without authentication."""
    response = unauthed_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_requires_auth(unauthed_client):
    """API endpoints should reject requests without auth."""
    response = unauthed_client.get("/api/v1/projects")
    assert response.status_code == 401
    assert "Authorization" in response.json()["detail"]


def test_api_rejects_invalid_key(unauthed_client):
    """API endpoints should reject invalid API keys."""
    response = unauthed_client.get(
        "/api/v1/projects",
        headers={"Authorization": "Bearer invalid-key-12345"},
    )
    assert response.status_code == 403
    assert "Invalid" in response.json()["detail"]


def test_api_rejects_malformed_header(unauthed_client):
    """API endpoints should reject non-Bearer auth headers."""
    response = unauthed_client.get(
        "/api/v1/projects",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert response.status_code == 401


def test_api_accepts_valid_key(client):
    """API endpoints should accept valid API keys."""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200


def test_authenticated_create_project(client):
    """Authenticated requests should work normally."""
    response = client.post("/api/v1/projects", json={"name": "Auth Test"})
    assert response.status_code == 201
    assert response.json()["name"] == "Auth Test"
