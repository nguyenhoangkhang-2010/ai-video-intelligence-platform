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

from pydantic import Field
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


class AppSettings(BaseSettings):
    """Application metadata."""

    name: str = "AI Video Intelligence Platform"

    version: str = "0.1.0"

    environment: Literal[
        "development",
        "testing",
        "production",
    ] = "development"

    debug: bool = True

    api_prefix: str = "/api/v1"

    docs_url: str = "/docs"

    redoc_url: str = "/redoc"

    openapi_url: str = "/openapi.json"


# =============================================================================
# Server
# =============================================================================


class ServerSettings(BaseSettings):
    """FastAPI server settings."""

    host: str = "0.0.0.0"

    port: int = 8000

    workers: int = 1

    reload: bool = True

    timeout: int = 300


# =============================================================================
# Security
# =============================================================================


class SecuritySettings(BaseSettings):
    """Security configuration."""

    secret_key: str = Field(
        default="CHANGE_ME",
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


class DatabaseSettings(BaseSettings):
    """PostgreSQL configuration."""

    host: str = "localhost"

    port: int = 5432

    username: str = "postgres"

    password: str = "postgres"

    database: str = "video_ai"

    echo: bool = False

    pool_size: int = 10

    max_overflow: int = 20

    @property
    def url(self) -> str:
        """Return SQLAlchemy connection URL."""

        return (
            "postgresql+psycopg://"
            f"{self.username}:{self.password}"
            f"@{self.host}:{self.port}"
            f"/{self.database}"
        )