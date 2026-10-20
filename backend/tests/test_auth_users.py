from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings
from app.core.security import verify_password
from app.models import User

from tests.conftest import login_user, register_user


def test_register_duplicate_email_and_never_returns_hash(client, db):
    response = register_user(client, role="admin", is_active=False)
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "user"
    assert body["is_active"] is True
    assert "password_hash" not in body
    stored_user = db.query(User).filter_by(email="user@example.com").one()
    assert stored_user.password_hash != "user-test-password-123"
    assert verify_password("user-test-password-123", stored_user.password_hash)

    duplicate = register_user(client, email=" USER@example.com ")
    assert duplicate.status_code == 409


def test_login_and_protected_identity(client):
    assert register_user(client).status_code == 201
    bad_login = login_user(client, password="wrong-password")
    assert bad_login.status_code == 401

    login = login_user(client)
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert "access_token" in login.json()
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/auth/me", headers=headers).json()["email"] == "user@example.com"
    assert client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"}
    ).status_code == 401
    expired_token = jwt.encode(
        {
            "sub": "1",
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(seconds=1),
        },
        get_settings().jwt_secret_key.get_secret_value(),
        algorithm="HS256",
    )
    assert client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    ).status_code == 401


def test_inactive_account_cannot_login_or_use_existing_token(client, db):
    register_user(client)
    login = login_user(client)
    token = login.json()["access_token"]
    user = db.query(User).filter_by(email="user@example.com").one()
    user.is_active = False
    db.commit()

    assert login_user(client).status_code == 403
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_profile_update_and_password_change(client):
    register_user(client)
    token = login_user(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    update = client.patch(
        "/api/users/me",
        json={"full_name": "Updated Name"},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["full_name"] == "Updated Name"
    assert client.patch(
        "/api/users/me",
        json={"full_name": None},
        headers=headers,
    ).status_code == 422

    change = client.post(
        "/api/users/me/change-password",
        json={
            "current_password": "user-test-password-123",
            "new_password": "user-new-password-123",
        },
        headers=headers,
    )
    assert change.status_code == 204
    assert login_user(client, password="user-new-password-123").status_code == 200
    assert login_user(client).status_code == 401


def test_invalid_registration_input(client):
    too_short = register_user(client, password="short")
    assert too_short.status_code == 422
    invalid_email = register_user(client, email="not-an-email")
    assert invalid_email.status_code == 422


def test_login_rate_limit(client):
    for _ in range(5):
        assert login_user(client, email="missing@example.com").status_code == 401
    limited = login_user(client, email="missing@example.com")
    assert limited.status_code == 429
