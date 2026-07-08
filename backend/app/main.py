"""
Application entry point.

AI Video Intelligence Platform Backend
"""
from fastapi import FastAPI

from app.config.settings import settings
from app.api import api_router
from app.core.startup import lifespan
from app.middleware.cors import setup_cors
from app.middleware.logging import setup_logging_middleware
from app.middleware.request_id import setup_request_id_middleware

def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    Returns:
        FastAPI: configured application instance
    """
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    # Middleware
    setup_cors(application)
    setup_request_id_middleware(application)
    setup_logging_middleware(application)
    # API routes
    application.include_router(
        api_router,
        prefix=settings.API_PREFIX,
    )
    return application

app = create_application()