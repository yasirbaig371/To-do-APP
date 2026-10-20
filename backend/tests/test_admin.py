from app.models import User, UserRole
from tests.conftest import login_user, register_user


def admin_headers(client):
    result = login_user(
        client,
        email="admin@example.com",
        password="Admin-test-password-123",
    )
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


def test_admin_endpoints_require_admin(client):
    register_user(client)
    user_headers = {
        "Authorization": f"Bearer {login_user(client).json()['access_token']}"
    }
    assert client.get("/api/admin/users", headers=user_headers).status_code == 403
    assert client.get("/api/admin/statistics", headers=user_headers).status_code == 403


def test_admin_list_serializes_phase_one_development_seed(client, db, admin_user):
    seeded = User(
        full_name="Demo User",
        email="demo.user@example.test",
        password_hash="NOT_A_REAL_PASSWORD_HASH_DO_NOT_USE_FOR_AUTH",
    )
    db.add(seeded)
    db.commit()

    response = client.get("/api/admin/users", headers=admin_headers(client))
    assert response.status_code == 200
    assert any(user["email"] == "demo.user@example.test" for user in response.json())
    assert login_user(client, email="demo.user@example.test").status_code == 401


def test_admin_search_management_statistics_and_last_admin_guard(
    client, db, admin_user
):
    register_user(client, email="managed@example.com")
    headers = admin_headers(client)
    users = client.get(
        "/api/admin/users?search=MANAGED&is_active=true&limit=10",
        headers=headers,
    )
    assert users.status_code == 200
    assert [user["email"] for user in users.json()] == ["managed@example.com"]

    managed_id = users.json()[0]["id"]
    role_change = client.patch(
        f"/api/admin/users/{managed_id}/role",
        json={"role": "admin"},
        headers=headers,
    )
    assert role_change.status_code == 200
    assert role_change.json()["role"] == "admin"

    admin_user.is_active = False
    db.commit()
    headers = {
        "Authorization": (
            "Bearer "
            + login_user(client, email="managed@example.com").json()["access_token"]
        )
    }
    last_admin = client.patch(
        f"/api/admin/users/{managed_id}/role",
        json={"role": "user"},
        headers=headers,
    )
    assert last_admin.status_code == 409
    last_admin_deactivation = client.patch(
        f"/api/admin/users/{managed_id}/status",
        json={"is_active": False},
        headers=headers,
    )
    assert last_admin_deactivation.status_code == 409
    second_admin = db.query(User).filter_by(id=managed_id).one()
    assert second_admin.role == UserRole.ADMIN

    admin_user.is_active = True
    db.commit()
    deactivated = client.patch(
        f"/api/admin/users/{managed_id}/status",
        json={"is_active": False},
        headers=headers,
    )
    assert deactivated.status_code == 200
    details = client.get(
        f"/api/admin/users/{managed_id}",
        headers=admin_headers(client),
    )
    assert details.status_code == 200
    assert details.json()["is_active"] is False

    stats = client.get("/api/admin/statistics", headers=admin_headers(client))
    assert stats.status_code == 200
    assert stats.json()["total_users"] == 2
    assert stats.json()["total_admins"] == 2
