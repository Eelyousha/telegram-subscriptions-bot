"""Application configuration."""
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


settings = Settings()
