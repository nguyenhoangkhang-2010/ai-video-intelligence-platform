"""
Application lifecycle management.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Execute startup and shutdown events.
    """
    # Startup
    print(
        f"Starting {settings.PROJECT_NAME}..."
    )
    print(
        f"Environment: {settings.ENVIRONMENT}"
    )
    yield
    # Shutdown
    print(
        "Application shutting down..."
    )