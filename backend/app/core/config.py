"""
Application configuration using Pydantic Settings.
Reads from environment variables and .env files.
All secrets must be provided via environment — never hard-coded.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    APP_NAME: str = "Stock Financial Analysis Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # ------------------------------------------------------------------ #
    # API
    # ------------------------------------------------------------------ #
    API_V1_PREFIX: str = "/api/v1"
    # Comma-separated list of trusted origins for CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    # ------------------------------------------------------------------ #
    # Database (PostgreSQL — async via asyncpg)
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/finplatform"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False  # Set True only in dev for SQL debugging

    # Sync URL used by Alembic migrations (psycopg2)
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/finplatform"

    # ------------------------------------------------------------------ #
    # Redis
    # ------------------------------------------------------------------ #
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_MAX_CONNECTIONS: int = 50

    # Cache TTLs (seconds)
    CACHE_TTL_STOCK_QUOTE: int = 15          # 15 s — near real-time
    CACHE_TTL_FINANCIAL_STATEMENTS: int = 86400  # 24 h
    CACHE_TTL_ANALYTICS: int = 14400         # 4 h
    CACHE_TTL_COMPANY_PROFILE: int = 43200   # 12 h
    CACHE_TTL_SEARCH_RESULTS: int = 300      # 5 min

    # ------------------------------------------------------------------ #
    # Authentication / JWT
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_SECRETS_MANAGER"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48

    # ------------------------------------------------------------------ #
    # Financial Modeling Prep (FMP)
    # ------------------------------------------------------------------ #
    FMP_API_KEY: str = ""
    FMP_BASE_URL: str = "https://financialmodelingprep.com/api/v3"
    FMP_BASE_URL_STABLE: str = "https://financialmodelingprep.com/stable"
    FMP_TIMEOUT_SECONDS: int = 30
    FMP_MAX_RETRIES: int = 3
    FMP_RETRY_BACKOFF_SECONDS: float = 1.0

    # ------------------------------------------------------------------ #
    # Celery
    # ------------------------------------------------------------------ #
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ------------------------------------------------------------------ #
    # Email
    # ------------------------------------------------------------------ #
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: EmailStr = "noreply@finplatform.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # ------------------------------------------------------------------ #
    # Rate Limiting
    # ------------------------------------------------------------------ #
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE: int = 10

    # ------------------------------------------------------------------ #
    # Security
    # ------------------------------------------------------------------ #
    BCRYPT_ROUNDS: int = 12
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # ------------------------------------------------------------------ #
    # Sentry
    # ------------------------------------------------------------------ #
    SENTRY_DSN: str = ""

    # ------------------------------------------------------------------ #
    # Logging
    # ------------------------------------------------------------------ #
    LOG_LEVEL: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached singleton Settings instance.
    Using lru_cache ensures the .env file is only read once per process.
    """
    return Settings()


settings = get_settings()
