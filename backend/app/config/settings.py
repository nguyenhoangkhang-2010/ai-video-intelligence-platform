"""
Application settings.

This module centralizes every configuration used across the
AI Video Intelligence Platform.

Environment variables are loaded from `.env`
and validated using Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# =============================================================================
# Paths
# =============================================================================

# backend/app/config/settings.py
#              ↑
# parents[0] = config
# parents[1] = app
# parents[2] = backend
# parents[3] = project root

PROJECT_ROOT = Path(__file__).resolve().parents[3]

ENV_FILE = PROJECT_ROOT / ".env"

BACKEND_DIR = PROJECT_ROOT / "backend"

AI_DIR = PROJECT_ROOT / "ai"

DATA_DIR = PROJECT_ROOT / "data"

STORAGE_DIR = PROJECT_ROOT / "storage"

LOG_DIR = PROJECT_ROOT / "logs"

UPLOAD_DIR = STORAGE_DIR / "uploads"

TEMP_DIR = STORAGE_DIR / "temp"

CACHE_DIR = STORAGE_DIR / "cache"

# =============================================================================
# Application
# =============================================================================
class BaseConfig(BaseSettings):
    """Base configuration shared by all settings."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

class AppSettings(BaseConfig):
    """Application metadata."""
    name: str = Field(
        default="AI Video Intelligence Platform",
        alias="APP_NAME",
    )

    version: str = Field(
        default="0.1.0",
        alias="APP_VERSION",
    )
    environment: Literal[
        "development",
        "testing",
        "production",
    ] = Field(
        default="development",
        alias="ENVIRONMENT",
    )

    debug: bool = Field(
        default=True,
        alias="DEBUG",
    )

    api_prefix: str = "/api/v1"

    docs_url: str = "/docs"

    redoc_url: str = "/redoc"

    openapi_url: str = "/openapi.json"


# =============================================================================
# Server
# =============================================================================
class ServerSettings(BaseConfig):
    """FastAPI server settings."""
    host: str = Field(
        default="0.0.0.0",
        alias="HOST",
    )

    port: int = Field(
        default=8000,
        alias="PORT",
    )
    workers: int = 1
    reload: bool = True
    timeout: int = 300
    
# =============================================================================
# Security
# =============================================================================
class SecuritySettings(BaseConfig):
    """Security configuration."""
    secret_key: str = Field(
        ...,
        alias="SECRET_KEY",
        min_length=32,
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# =============================================================================
# Database
# =============================================================================
class DatabaseSettings(BaseConfig):
    """PostgreSQL configuration."""
    database_url: str = Field(
        ...,
        alias="DATABASE_URL",
    )
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    
    @property
    def url(self) -> str:
        """Return database URL."""
        return self.database_url

# =============================================================================
# Global Settings Instance
# =============================================================================
class Settings(BaseModel):
    """
    Main application settings.
    Aggregates all configuration sections.
    """
    app: AppSettings = Field(default_factory=AppSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

@lru_cache
def get_settings() -> Settings:
    """
    Return cached settings instance.
    """
    return Settings()
settings = get_settings()
