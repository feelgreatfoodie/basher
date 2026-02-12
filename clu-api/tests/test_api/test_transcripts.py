import io

from tests.conftest import SAMPLE_TRANSCRIPT


def test_upload_transcript(client):
    # Create project first
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    # Upload transcript
    response = client.post(
        f"/api/v1/projects/{project_id}/transcripts",
        files={"file": ("meeting.txt", io.BytesIO(SAMPLE_TRANSCRIPT.encode()), "text/plain")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "meeting.txt"
    assert data["transcript_type"] == "meeting"
    assert data["word_count"] > 0


def test_upload_transcript_project_not_found(client):
    response = client.post(
        "/api/v1/projects/nonexistent/transcripts",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 404


def test_list_transcripts(client):
    project = client.post("/api/v1/projects", json={"name": "Test"}).json()
    project_id = project["id"]

    client.post(
        f"/api/v1/projects/{project_id}/transcripts",
        files={"file": ("meeting1.txt", io.BytesIO(SAMPLE_TRANSCRIPT.encode()), "text/plain")},
    )
    client.post(
        f"/api/v1/projects/{project_id}/transcripts",
        files={"file": ("meeting2.txt", io.BytesIO(SAMPLE_TRANSCRIPT.encode()), "text/plain")},
    )

    response = client.get(f"/api/v1/projects/{project_id}/transcripts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_list_transcripts_project_not_found(client):
    response = client.get("/api/v1/projects/nonexistent/transcripts")
    assert response.status_code == 404
