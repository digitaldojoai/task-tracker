def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_task(client):
    response = client.post("/tasks", json={"title": "Write report"})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Write report"
    assert body["status"] == "ToDo"
    assert body["priority"] == "Medium"
    assert "id" in body


def test_list_tasks_empty(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_after_create(client):
    client.post("/tasks", json={"title": "Task A"})
    client.post("/tasks", json={"title": "Task B"})
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_task_by_id(client):
    created = client.post("/tasks", json={"title": "Task A"}).json()
    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_task_not_found(client):
    response = client.get("/tasks/does-not-exist")
    assert response.status_code == 404


def test_update_task(client):
    created = client.post("/tasks", json={"title": "Task A"}).json()
    response = client.patch(f"/tasks/{created['id']}", json={"status": "InProgress"})
    assert response.status_code == 200
    assert response.json()["status"] == "InProgress"
    assert response.json()["title"] == "Task A"


def test_update_task_not_found(client):
    response = client.patch("/tasks/does-not-exist", json={"status": "Done"})
    assert response.status_code == 404


def test_delete_task(client):
    created = client.post("/tasks", json={"title": "Task A"}).json()
    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_delete_task_not_found(client):
    response = client.delete("/tasks/does-not-exist")
    assert response.status_code == 404


def test_filter_tasks_by_status(client):
    client.post("/tasks", json={"title": "Task A", "status": "Done"})
    client.post("/tasks", json={"title": "Task B", "status": "ToDo"})
    response = client.get("/tasks", params={"status": "Done"})
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Task A"
