from tests.conftest import login_user, register_user


def authenticated_headers(client, email):
    result = login_user(client, email=email)
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


def test_task_crud_and_owner_isolation(client):
    register_user(client, email="owner@example.com")
    owner_headers = authenticated_headers(client, "owner@example.com")
    created = client.post(
        "/api/tasks",
        json={
            "title": "  Write tests  ",
            "description": "Check ownership",
            "priority": "high",
        },
        headers=owner_headers,
    )
    assert created.status_code == 201
    task = created.json()
    assert task["title"] == "Write tests"
    assert task["status"] == "pending"

    assert client.get(f"/api/tasks/{task['id']}", headers=owner_headers).status_code == 200
    updated = client.patch(
        f"/api/tasks/{task['id']}",
        json={"status": "completed"},
        headers=owner_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["completed_at"] is not None
    reopened = client.patch(
        f"/api/tasks/{task['id']}",
        json={"status": "pending"},
        headers=owner_headers,
    )
    assert reopened.json()["completed_at"] is None

    register_user(client, email="other@example.com")
    other_headers = authenticated_headers(client, "other@example.com")
    assert client.get(
        f"/api/tasks/{task['id']}", headers=other_headers
    ).status_code == 404
    assert client.patch(
        f"/api/tasks/{task['id']}",
        json={"title": "Stolen"},
        headers=other_headers,
    ).status_code == 404
    assert client.delete(
        f"/api/tasks/{task['id']}", headers=other_headers
    ).status_code == 404
    assert client.delete(
        f"/api/tasks/{task['id']}", headers=owner_headers
    ).status_code == 204


def test_task_filter_search_sort_pagination_and_stats(client):
    register_user(client)
    headers = authenticated_headers(client, "user@example.com")
    for title, status_value, priority in [
        ("Plan launch", "pending", "high"),
        ("Write report", "in_progress", "medium"),
        ("Launch review", "completed", "high"),
    ]:
        response = client.post(
            "/api/tasks",
            json={"title": title, "status": status_value, "priority": priority},
            headers=headers,
        )
        assert response.status_code == 201

    filtered = client.get(
        "/api/tasks?status=completed&priority=high&search=REVIEW",
        headers=headers,
    )
    assert filtered.status_code == 200
    assert [task["title"] for task in filtered.json()] == ["Launch review"]

    page = client.get("/api/tasks?limit=1&offset=1&sort_by=title&sort_order=asc", headers=headers)
    assert page.status_code == 200
    assert len(page.json()) == 1
    assert client.get("/api/tasks?limit=101", headers=headers).status_code == 422
    assert client.get("/api/tasks?sort_by=password_hash", headers=headers).status_code == 422

    stats = client.get("/api/users/me/statistics", headers=headers).json()
    assert stats == {"total": 3, "pending": 1, "in_progress": 1, "completed": 1}


def test_task_validation_and_authentication_required(client):
    assert client.get("/api/tasks").status_code == 401
    register_user(client)
    headers = authenticated_headers(client, "user@example.com")
    assert client.post("/api/tasks", json={"title": "  "}, headers=headers).status_code == 422
    assert client.post(
        "/api/tasks",
        json={"title": "Task", "status": "unknown"},
        headers=headers,
    ).status_code == 422
    assert client.patch(
        "/api/tasks/1",
        json={"status": None},
        headers=headers,
    ).status_code == 422
