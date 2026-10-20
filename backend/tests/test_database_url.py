import pytest
from sqlalchemy import create_engine

from app.core.config import normalize_database_url


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql://todo_user:encoded%40password@db.example.test/todo?sslmode=require",
        "postgres://todo_user:encoded%40password@db.example.test/todo?sslmode=require",
        "postgresql+psycopg://todo_user:encoded%40password@db.example.test/todo?sslmode=require",
    ],
)
def test_postgresql_urls_use_psycopg_3_without_losing_connection_options(
    database_url,
):
    url = normalize_database_url(database_url)

    assert url.drivername == "postgresql+psycopg"
    assert url.username == "todo_user"
    assert url.password == "encoded@password"
    assert url.host == "db.example.test"
    assert url.database == "todo"
    assert url.query == {"sslmode": "require"}
    engine = create_engine(url)
    try:
        assert engine.dialect.driver == "psycopg"
    finally:
        engine.dispose()


def test_sqlite_url_remains_unchanged():
    url = normalize_database_url("sqlite:///./test.db")

    assert url.drivername == "sqlite"
