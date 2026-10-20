import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import Task, TaskPriority, TaskStatus, User, UserRole


def auth_headers(client, email="user@example.com", password="user-test-password-123"):
    login = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_chat_list_my_tasks_uses_allowed_tool(client, db, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    get_settings.cache_clear()

    user = User(
        full_name="Chat User",
        email="user@example.com",
        password_hash=hash_password("user-test-password-123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    task = Task(
        title="Reply to project brief",
        description="Draft the summary",
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        owner_id=user.id,
    )
    db.add(task)
    db.commit()

    tool_call = MagicMock()
    tool_call.function.name = "list_my_tasks"
    tool_call.function.arguments = json.dumps({"status": "pending"})

    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[tool_call], content=None))]
    )

    with patch("app.api.routes.chat.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = fake_response
        response = client.post(
            "/api/chat",
            json={"message": "Show my pending tasks."},
            headers=auth_headers(client, email="user@example.com"),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tool_name"] == "list_my_tasks"
    assert payload["response"].startswith("I found")
    assert payload["tool_results"][0]["result"]["tasks"][0]["title"] == "Reply to project brief"


def test_chat_requires_confirmation_for_task_deletion(client, db, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    get_settings.cache_clear()

    user = User(
        full_name="Delete User",
        email="delete@example.com",
        password_hash=hash_password("user-test-password-123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    task = Task(
        title="Old upload task",
        description="Delete this later",
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        owner_id=user.id,
    )
    db.add(task)
    db.commit()

    tool_call = MagicMock()
    tool_call.function.name = "delete_my_task"
    tool_call.function.arguments = json.dumps({"task_id": task.id, "confirm": False})

    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[tool_call], content=None))]
    )

    with patch("app.api.routes.chat.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = fake_response
        response = client.post(
            "/api/chat",
            json={"message": "Delete my old upload task."},
            headers=auth_headers(client, email="delete@example.com", password="user-test-password-123"),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["requires_confirmation"] is True
    assert payload["tool_name"] == "delete_my_task"
    assert payload["tool_results"][0]["result"]["requires_confirmation"] is True


def test_chat_rejects_admin_tool_for_regular_user(client, db, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    get_settings.cache_clear()

    user = User(
        full_name="Member User",
        email="member@example.com",
        password_hash=hash_password("user-test-password-123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    tool_call = MagicMock()
    tool_call.function.name = "list_users"
    tool_call.function.arguments = json.dumps({})

    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[tool_call], content=None))]
    )

    with patch("app.api.routes.chat.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = fake_response
        response = client.post(
            "/api/chat",
            json={"message": "Show me all registered users."},
            headers=auth_headers(client, email="member@example.com", password="user-test-password-123"),
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Administrator access required"


def test_chat_uses_openrouter_configuration(client, db, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "liquid/lfm-2.5-2.6b:free")
    get_settings.cache_clear()

    user = User(
        full_name="OpenRouter User",
        email="openrouter@example.com",
        password_hash=hash_password("user-test-password-123"),
    )
    db.add(user)
    db.commit()

    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=None, content="Ready."))]
    )

    with patch("app.api.routes.chat.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = fake_response
        response = client.post(
            "/api/chat",
            json={"message": "Hello."},
            headers=auth_headers(client, email="openrouter@example.com"),
        )

    assert response.status_code == 200
    assert response.json()["response"] == "Ready."
    mock_openai.assert_called_once_with(
        api_key="test-openrouter-key",
        base_url="https://openrouter.ai/api/v1",
    )
    assert mock_openai.return_value.chat.completions.create.call_args.kwargs["model"] == (
        "liquid/lfm-2.5-2.6b:free"
    )


def test_chat_executes_delete_after_explicit_confirmation(client, db, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    get_settings.cache_clear()

    user = User(
        full_name="Confirmed User",
        email="confirmed@example.com",
        password_hash=hash_password("user-test-password-123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    task = Task(
        title="Final draft",
        description="Delete after confirm",
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        owner_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    tool_call = MagicMock()
    tool_call.function.name = "delete_my_task"
    tool_call.function.arguments = json.dumps({"task_id": task.id, "confirm": False})

    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[tool_call], content=None))]
    )

    with patch("app.api.routes.chat.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = fake_response
        first = client.post(
            "/api/chat",
            json={"message": "Delete my final draft."},
            headers=auth_headers(client, email="confirmed@example.com", password="user-test-password-123"),
        )
        second = client.post(
            "/api/chat",
            json={"message": "Delete my final draft.", "confirm": True},
            headers=auth_headers(client, email="confirmed@example.com", password="user-test-password-123"),
        )

    assert first.status_code == 200
    assert first.json()["requires_confirmation"] is True
    assert second.status_code == 200
    assert second.json()["tool_name"] == "delete_my_task"
    assert second.json()["response"] == "Task deleted successfully."
    db.expunge_all()
    assert db.get(Task, task.id) is None
