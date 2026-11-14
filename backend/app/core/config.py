from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Project Info
    PROJECT_NAME: str = "Digital Ecosystem Intelligence Platform"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")
    DEBUG: bool = Field(default=False, alias="DEBUG")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://ecosystem:ecosystem_dev@localhost:5432/ecosystem_db",
        alias="DATABASE_URL",
    )

    # Security & Sessions
    SESSION_SECRET: str = Field(
        default="generate-a-64-char-random-hex-string-here-minimum-32-chars",
        alias="SESSION_SECRET",
    )
    FRONTEND_ORIGIN: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Cookie Configuration
    COOKIE_NAME: str = "session_token"
    COOKIE_SECURE: bool = Field(default=False, alias="COOKIE_SECURE")
    COOKIE_SAMESITE: str = Field(default="lax", alias="COOKIE_SAMESITE")
    COOKIE_DOMAIN: str | None = Field(default=None, alias="COOKIE_DOMAIN")
    SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 7  # 7 days

    # S3-Compatible Object Storage
    S3_ENDPOINT_URL: str | None = Field(default=None, alias="S3_ENDPOINT_URL")
    S3_BUCKET_NAME: str | None = Field(default="ecosystem-uploads-dev", alias="S3_BUCKET_NAME")
    S3_ACCESS_KEY_ID: str | None = Field(default=None, alias="S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY: str | None = Field(default=None, alias="S3_SECRET_ACCESS_KEY")
    S3_REGION: str = Field(default="auto", alias="S3_REGION")

    # LLM Settings
    LLM_PROVIDER: str = Field(default="gemini", alias="LLM_PROVIDER")
    LLM_API_KEY: str | None = Field(default=None, alias="LLM_API_KEY")
    LLM_MODEL: str = Field(default="gemini-2.5-flash", alias="LLM_MODEL")

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql+psycopg://"):
            return url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
