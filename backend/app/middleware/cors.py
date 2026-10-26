"""
CORS middleware configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings

def setup_cors(app: FastAPI) -> None:
    """
    Configure Cross-Origin Resource Sharing.

    Origins are environment-driven (settings.security.cors_origins /
    CORS_ORIGINS) rather than hardcoded, so production deployments can
    restrict this to their real public frontend origin(s) without a
    code change. Defaults to the local frontend dev server origins
    when unset.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=[
            "*",
        ],
        allow_headers=[
            "*",
        ],
    )