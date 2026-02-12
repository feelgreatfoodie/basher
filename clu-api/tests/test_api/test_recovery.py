"""Tests for job recovery (retry failed analyses)."""

import json
from unittest.mock import patch

from app.models import Analysis
from tests.conftest import TEST_TENANT_ID


def test_retry_failed_analysis_with_checkpoint(client, db):
    """Retry endpoint should accept a failed analysis with a checkpoint."""
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    analysis = Analysis(
        project_id=project_id,
        status="failed",
        last_checkpoint="extraction_complete",
        error_message="Synthesis timed out",
        tenant_id=TEST_TENANT_ID,
    )
    db.add(analysis)
    db.commit()

    with patch("app.api.analysis.recover_analysis") as mock_recover:
        response = client.post(f"/api/v1/projects/{project_id}/analysis/retry")
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "recovering"
        assert data["last_checkpoint"] == "extraction_complete"
        mock_recover.assert_called_once()


def test_retry_not_failed_returns_409(client, db):
    """Retry should reject analyses that aren't in 'failed' status."""
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    analysis = Analysis(
        project_id=project_id,
        status="complete",
        results_json=json.dumps({"summary": {}}),
        tenant_id=TEST_TENANT_ID,
    )
    db.add(analysis)
    db.commit()

    response = client.post(f"/api/v1/projects/{project_id}/analysis/retry")
    assert response.status_code == 409
    assert "not 'failed'" in response.json()["detail"]


def test_retry_no_checkpoint_returns_409(client, db):
    """Retry should reject failed analyses with no checkpoint."""
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    analysis = Analysis(
        project_id=project_id,
        status="failed",
        last_checkpoint=None,
        error_message="Failed before any checkpoint",
        tenant_id=TEST_TENANT_ID,
    )
    db.add(analysis)
    db.commit()

    response = client.post(f"/api/v1/projects/{project_id}/analysis/retry")
    assert response.status_code == 409
    assert "no checkpoint" in response.json()["detail"]


def test_retry_project_not_found(client):
    """Retry on nonexistent project should 404."""
    response = client.post("/api/v1/projects/nonexistent/analysis/retry")
    assert response.status_code == 404


def test_retry_no_analysis_returns_404(client, db):
    """Retry on a project with no analyses should 404."""
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    response = client.post(f"/api/v1/projects/{project_id}/analysis/retry")
    assert response.status_code == 404
