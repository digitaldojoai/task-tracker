def test_create_task_with_tags(client):
    response = client.post("/tasks", json={"title": "Task A", "tags": ["urgent", " backend "]})
    assert response.status_code == 201
    assert response.json()["tags"] == ["urgent", "backend"]


def test_reject_empty_tag(client):
    response = client.post("/tasks", json={"title": "Task A", "tags": ["urgent", "   "]})
    assert response.status_code == 422


def test_reject_too_many_tags(client):
    response = client.post("/tasks", json={"title": "Task A", "tags": [f"t{i}" for i in range(11)]})
    assert response.status_code == 422


def test_update_tags(client):
    created = client.post("/tasks", json={"title": "Task A"}).json()
    response = client.patch(f"/tasks/{created['id']}", json={"tags": ["design", "ui"]})
    assert response.status_code == 200
    assert response.json()["tags"] == ["design", "ui"]


def test_filter_by_tag(client):
    client.post("/tasks", json={"title": "Task A", "tags": ["backend"]})
    client.post("/tasks", json={"title": "Task B", "tags": ["frontend"]})

    response = client.get("/tasks", params={"tag": "backend"})
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Task A"


def test_tags_preserved_after_unrelated_update(client):
    created = client.post("/tasks", json={"title": "Task A", "tags": ["keep-me"]}).json()
    response = client.patch(f"/tasks/{created['id']}", json={"status": "InProgress"})
    assert response.status_code == 200
    assert response.json()["tags"] == ["keep-me"]
