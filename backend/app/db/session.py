from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings, normalize_database_url

settings = get_settings()
database_url = normalize_database_url(settings.database_url)
is_postgresql = database_url.drivername.startswith("postgresql+")
connect_args = (
    {"options": "-c timezone=UTC"}
    if is_postgresql
    else {}
)
engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


if is_postgresql:
    @event.listens_for(engine, "connect")
    def set_utc_timezone(dbapi_connection: object, connection_record: object) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("SET TIME ZONE 'UTC'")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
