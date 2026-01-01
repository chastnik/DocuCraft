"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "DocuCraft"
    app_env: str = "development"
    debug: bool = True
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str
    database_url_sync: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # GitHub OAuth
    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_webhook_secret: str | None = None

    # AI Providers
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ai_provider: str = "openai"  # openai or anthropic

    # CORS
    # Accept both string (comma-separated) and list formats
    cors_origins: str | List[str] = "http://localhost:3000,http://localhost:5173"

    # File Storage
    storage_type: str = "local"  # local or s3
    storage_path: str = "./storage"
    s3_bucket: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(self.cors_origins, str):
            # Handle empty string
            if not self.cors_origins.strip():
                return ["http://localhost:3000", "http://localhost:5173"]
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        elif isinstance(self.cors_origins, list):
            return self.cors_origins
        else:
            # Fallback to default
            return ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()

