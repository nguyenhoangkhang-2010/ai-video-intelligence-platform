"""
Application entry point.

AI Video Intelligence Platform Backend
"""

from fastapi import FastAPI

from app.api import api_router
from app.config.settings import settings
from app.core.startup import lifespan
from app.middleware.cors import setup_cors
from app.middleware.logging import setup_logging_middleware
from app.middleware.request_id import setup_request_id_middleware

def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    Returns:
        FastAPI: Configured application instance.
    """
    application = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        debug=settings.app.debug,
        docs_url=settings.app.docs_url,
        redoc_url=settings.app.redoc_url,
        openapi_url=settings.app.openapi_url,
        lifespan=lifespan,
    )
    # Middleware
    setup_cors(application)
    setup_request_id_middleware(application)
    setup_logging_middleware(application)
    # API routes
    application.include_router(
        api_router,
        prefix=settings.app.api_prefix,
    )
    return application

app = create_application()

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    """
    return {
        "name": settings.app.name,
        "version": settings.app.version,
        "environment": settings.app.environment,
        "docs": settings.app.docs_url,
        "health": f"{settings.app.api_prefix}/health",
    }