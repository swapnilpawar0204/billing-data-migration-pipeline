from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}


class Settings(BaseSettings):
    """Application settings loaded from the environment / .env file.

    In production (``APP_ENV=production``) the database password and the
    service API key are mandatory so the service can never start unprotected.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Inbound authentication for this service's own API (X-API-Key header).
    service_api_key: str = Field(default="", alias="SERVICE_API_KEY")

    # Outbound: the external billing API we ingest from.
    api_base_url: str = Field(
        default="https://example.com/api/billing", alias="API_BASE_URL"
    )
    api_key: str = Field(default="", alias="API_KEY")
    api_timeout_seconds: float = Field(default=10.0, gt=0, alias="API_TIMEOUT_SECONDS")
    api_max_retries: int = Field(default=3, ge=0, le=10, alias="API_MAX_RETRIES")

    mysql_host: str = Field(default="localhost", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, ge=1, le=65535, alias="MYSQL_PORT")
    mysql_database: str = Field(default="billing", alias="MYSQL_DATABASE")
    mysql_user: str = Field(default="app_user", alias="MYSQL_USER")
    mysql_password: str = Field(default="", alias="MYSQL_PASSWORD")

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        return value.strip() or "development"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.strip().upper() or "INFO"
        if normalized not in _LOG_LEVELS:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(_LOG_LEVELS)}")
        return normalized

    @model_validator(mode="after")
    def require_secrets_in_production(self) -> "Settings":
        if self.is_production:
            missing = [
                name
                for name, value in (
                    ("MYSQL_PASSWORD", self.mysql_password),
                    ("SERVICE_API_KEY", self.service_api_key),
                )
                if not value
            ]
            if missing:
                raise ValueError(
                    f"{', '.join(missing)} must be set when APP_ENV=production"
                )
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for reuse throughout the application."""
    return Settings()


settings = get_settings()
