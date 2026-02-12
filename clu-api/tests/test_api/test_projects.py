def test_create_project(client):
    response = client.post("/api/v1/projects", json={"name": "Test Project"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["id"]
    assert data["tenant_id"] is not None


def test_create_project_with_description(client):
    response = client.post(
        "/api/v1/projects",
        json={"name": "Test Project", "description": "A test project"},
    )
    assert response.status_code == 201
    assert response.json()["description"] == "A test project"


def test_list_projects(client):
    client.post("/api/v1/projects", json={"name": "Project 1"})
    client.post("/api/v1/projects", json={"name": "Project 2"})

    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["projects"]) == 2


def test_get_project(client):
    create_resp = client.post("/api/v1/projects", json={"name": "Test Project"})
    project_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Project"


def test_get_project_not_found(client):
    response = client.get("/api/v1/projects/nonexistent")
    assert response.status_code == 404
