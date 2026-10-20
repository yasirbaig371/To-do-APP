import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-with-at-least-32-characters"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"
os.environ["CORS_ORIGINS"] = '["http://localhost:5173"]'

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.db.base import Base
from app.main import app
from app.models import User, UserRole

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    del connection_record
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    limiter._storage.reset()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_user(db):
    admin = User(
        full_name="Test Administrator",
        email="admin@example.com",
        password_hash=hash_password("Admin-test-password-123"),
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def register_user(client, email="user@example.com", **fields):
    payload = {
        "full_name": "Test User",
        "email": email,
        "password": "user-test-password-123",
    }
    payload.update(fields)
    return client.post("/api/auth/register", json=payload)


def login_user(client, email="user@example.com", password="user-test-password-123"):
    return client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
