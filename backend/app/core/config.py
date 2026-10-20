from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url


def normalize_database_url(database_url: str) -> URL:
    url = make_url(database_url)
    if url.drivername.partition("+")[0] in {"postgres", "postgresql"}:
        return url.set(drivername="postgresql+psycopg")
    return url


class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: SecretStr
    access_token_expire_minutes: int = 15
    cors_origins: list[str] = ["http://localhost:5173"]
    openrouter_api_key: SecretStr | None = None
    openrouter_model: str = "liquid/lfm-2.5-2.6b:free"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters")
        return value

    @field_validator("access_token_expire_minutes")
    @classmethod
    def validate_token_lifetime(cls, value: int) -> int:
        if not 1 <= value <= 1440:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 1440")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
