"""Tests for tenant isolation."""

import hashlib

from app.models.api_key import ApiKey
from tests.conftest import TEST_TENANT_ID


TENANT_B_KEY = "tenant-b-api-key"
TENANT_B_HASH = hashlib.sha256(TENANT_B_KEY.encode()).hexdigest()
TENANT_B_ID = "tenant-b-002"


def test_project_created_with_tenant_id(client, db):
    """Projects created via authenticated request should get the tenant_id."""
    response = client.post("/api/v1/projects", json={"name": "Tenant Test"})
    assert response.status_code == 201
    assert response.json()["tenant_id"] == TEST_TENANT_ID


def test_tenant_isolation_projects(client, db):
    """Tenant A should not see tenant B's projects."""
    # Create project as tenant A (via default client)
    client.post("/api/v1/projects", json={"name": "Tenant A Project"})

    # Create a tenant B API key
    api_key_b = ApiKey(
        key_hash=TENANT_B_HASH,
        tenant_id=TENANT_B_ID,
        name="Tenant B Key",
        is_active=True,
        rate_limit=100,
    )
    db.add(api_key_b)
    db.commit()

    # List projects as tenant B — should see nothing
    response = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {TENANT_B_KEY}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0

    # List as tenant A — should see the project
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_tenant_cannot_access_other_tenant_project(client, db):
    """Tenant A should get 404 when accessing tenant B's project."""
    # Create project as tenant A
    resp = client.post("/api/v1/projects", json={"name": "Private Project"})
    project_id = resp.json()["id"]

    # Create tenant B key
    api_key_b = ApiKey(
        key_hash=TENANT_B_HASH,
        tenant_id=TENANT_B_ID,
        name="Tenant B Key",
        is_active=True,
        rate_limit=100,
    )
    db.add(api_key_b)
    db.commit()

    # Access as tenant B — should get 404
    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {TENANT_B_KEY}"},
    )
    assert response.status_code == 404


def test_transcript_inherits_tenant_id(client, db):
    """Transcripts uploaded to a tenant's project should get the tenant_id."""
    resp = client.post("/api/v1/projects", json={"name": "Transcript Tenant Test"})
    project_id = resp.json()["id"]

    response = client.post(
        f"/api/v1/projects/{project_id}/transcripts",
        files={"file": ("test.txt", b"Alice: Hello\nBob: Hi", "text/plain")},
    )
    assert response.status_code == 201
    assert response.json()["tenant_id"] == TEST_TENANT_ID
