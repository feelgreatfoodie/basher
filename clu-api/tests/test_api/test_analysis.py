import json
from unittest.mock import patch

from app.models import Analysis, Transcript, Extraction


@patch("app.api.analysis.run_analysis_pipeline")
def test_trigger_analysis(mock_pipeline, client, db):
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    response = client.post(f"/api/v1/projects/{project_id}/analyze")
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "pending"
    assert data["project_id"] == project_id


def test_trigger_analysis_project_not_found(client):
    response = client.post("/api/v1/projects/nonexistent/analyze")
    assert response.status_code == 404


@patch("app.api.analysis.run_analysis_pipeline")
def test_get_analysis_status(mock_pipeline, client, db):
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    # Trigger analysis
    client.post(f"/api/v1/projects/{project_id}/analyze")

    response = client.get(f"/api/v1/projects/{project_id}/analysis/status")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_get_analysis_status_not_found(client):
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    response = client.get(f"/api/v1/projects/{project['id']}/analysis/status")
    assert response.status_code == 404


@patch("app.api.analysis.run_analysis_pipeline")
def test_get_analysis_results_not_complete(mock_pipeline, client, db):
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    client.post(f"/api/v1/projects/{project_id}/analyze")

    response = client.get(f"/api/v1/projects/{project_id}/analysis/results")
    assert response.status_code == 409


def test_get_analysis_results_complete(client, db):
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    # Manually create a completed analysis
    results = {"summary": {"totalTranscripts": 1}, "conflicts": [], "gaps": []}
    analysis = Analysis(
        project_id=project_id,
        status="complete",
        results_json=json.dumps(results),
    )
    db.add(analysis)
    db.commit()

    response = client.get(f"/api/v1/projects/{project_id}/analysis/results")
    assert response.status_code == 200
    assert response.json()["status"] == "complete"


def test_get_analysis_by_type(client, db):
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    results = {"summary": {"totalTranscripts": 2}, "conflicts": [{"topic": "API protocol"}]}
    analysis = Analysis(
        project_id=project_id,
        status="complete",
        results_json=json.dumps(results),
    )
    db.add(analysis)
    db.commit()

    response = client.get(f"/api/v1/projects/{project_id}/analysis/summary")
    assert response.status_code == 200
    assert response.json()["type"] == "summary"

    response = client.get(f"/api/v1/projects/{project_id}/analysis/conflicts")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_get_analysis_by_type_invalid(client, db):
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    results = {"summary": {}}
    analysis = Analysis(project_id=project_id, status="complete", results_json=json.dumps(results))
    db.add(analysis)
    db.commit()

    response = client.get(f"/api/v1/projects/{project_id}/analysis/invalid-type")
    assert response.status_code == 400


def test_get_extraction_confidence(client, db):
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    # Create a transcript and extraction with confidence
    transcript = Transcript(
        project_id=project_id,
        filename="test.txt",
        content="Alice: Let's use REST.",
        transcript_type="meeting",
        word_count=5,
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)

    extraction = Extraction(
        transcript_id=transcript.id,
        data_json='{"decisions": []}',
        confidence=0.85,
        model_used="claude-sonnet-4-5-20250929",
    )
    db.add(extraction)
    db.commit()

    response = client.get(f"/api/v1/projects/{project_id}/analysis/confidence")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == project_id
    assert data["average_confidence"] == 0.85
    assert len(data["extractions"]) == 1
    assert data["extractions"][0]["confidence"] == 0.85


def test_get_extraction_confidence_no_extractions(client, db):
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    response = client.get(f"/api/v1/projects/{project_id}/analysis/confidence")
    assert response.status_code == 404
