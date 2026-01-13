"""Application configuration."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str

    # Telegram Bot
    bot_token: str
    api_url: str = "http://api:8000"

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Scheduler
    notification_hour: int = 10

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Rate limiting
    throttle_rate: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function is cached to ensure a single Settings instance is used
    throughout the application lifecycle. It can be used as a FastAPI dependency
    or called directly.

    Returns:
        Settings instance

    Examples:
        As a FastAPI dependency:
        >>> @app.get("/")
        >>> def root(settings: Settings = Depends(get_settings)):
        >>>     return {"db": settings.database_url}

        Direct usage:
        >>> settings = get_settings()
        >>> print(settings.database_url)
    """
    return Settings()


# Global settings instance for backward compatibility
# Prefer using get_settings() for new code
settings = get_settings()
