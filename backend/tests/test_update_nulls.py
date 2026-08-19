"""Explicit-null handling on PATCH /tasks/{id}.

Omitting a field means "leave unchanged". Sending it as an explicit null is a
different request, and for non-nullable fields it must be rejected rather than
stored. assignee and due_date are the two fields where null legitimately means
"clear this value".
"""

import pytest


def _create(client, **overrides):
    payload = {"title": "Original title"}
    payload.update(overrides)
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


def test_update_title_to_null_rejected(client):
    task = _create(client)

    response = client.patch(f"/tasks/{task['id']}", json={"title": None})

    assert response.status_code == 422


def test_update_title_to_null_does_not_change_stored_task(client):
    task = _create(client)

    client.patch(f"/tasks/{task['id']}", json={"title": None})

    stored = client.get(f"/tasks/{task['id']}").json()
    assert stored["title"] == "Original title"


@pytest.mark.parametrize(
    "field, value",
    [
        ("description", "notes"),
        ("status", "InProgress"),
        ("priority", "High"),
        ("tags", ["urgent"]),
    ],
)
def test_non_nullable_fields_rejected_as_null(client, field, value):
    task = _create(client, **{field: value})

    response = client.patch(f"/tasks/{task['id']}", json={field: None})

    assert response.status_code == 422
    assert client.get(f"/tasks/{task['id']}").json()[field] == value


def test_assignee_and_due_date_can_be_cleared_with_null(client):
    task = _create(client, assignee="Dana", due_date="2030-01-01")

    response = client.patch(
        f"/tasks/{task['id']}", json={"assignee": None, "due_date": None}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assignee"] is None
    assert body["due_date"] is None


def test_omitted_fields_still_leave_task_unchanged(client):
    task = _create(client, description="notes", tags=["a"])

    response = client.patch(f"/tasks/{task['id']}", json={"status": "Done"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Done"
    assert body["title"] == "Original title"
    assert body["description"] == "notes"
    assert body["tags"] == ["a"]
