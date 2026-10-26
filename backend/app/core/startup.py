from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""

    # Startup
    yield

    # Shutdown