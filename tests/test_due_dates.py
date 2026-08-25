from datetime import date, timedelta

YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()


def test_create_task_with_valid_due_date(client):
    response = client.post("/tasks", json={"title": "Task A", "due_date": TOMORROW})
    assert response.status_code == 201
    body = response.json()
    assert body["due_date"] == TOMORROW
    assert body["overdue"] is False


def test_create_task_with_invalid_due_date_format(client):
    response = client.post("/tasks", json={"title": "Task A", "due_date": "not-a-date"})
    assert response.status_code == 422


def test_overdue_detection_for_past_due_incomplete_task(client):
    response = client.post("/tasks", json={"title": "Task A", "due_date": YESTERDAY})
    assert response.status_code == 201
    assert response.json()["overdue"] is True


def test_done_task_with_past_due_date_is_not_overdue(client):
    response = client.post(
        "/tasks", json={"title": "Task A", "due_date": YESTERDAY, "status": "Done"}
    )
    assert response.status_code == 201
    assert response.json()["overdue"] is False


def test_update_due_date(client):
    created = client.post("/tasks", json={"title": "Task A"}).json()
    response = client.patch(f"/tasks/{created['id']}", json={"due_date": TOMORROW})
    assert response.status_code == 200
    assert response.json()["due_date"] == TOMORROW


def test_filter_returns_only_overdue_tasks(client):
    client.post("/tasks", json={"title": "Overdue task", "due_date": YESTERDAY})
    client.post("/tasks", json={"title": "Future task", "due_date": TOMORROW})
    client.post("/tasks", json={"title": "No due date task"})

    response = client.get("/tasks", params={"overdue": "true"})
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Overdue task"
