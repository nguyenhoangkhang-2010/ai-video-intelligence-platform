"""
Application entry point.

AI Video Intelligence Platform Backend
"""

from fastapi import Depends, FastAPI, Response
from sqlalchemy.orm import Session

from app.api import api_router
from app.config.logging import setup_logging
from app.config.settings import settings
from app.core.metrics import render_metrics, setup_metrics_middleware, update_processing_jobs_gauge
from app.core.startup import lifespan
from app.database.session import get_db
from app.middleware.cors import setup_cors
from app.middleware.logging import setup_logging_middleware
from app.middleware.request_id import setup_request_id_middleware

# Configured before anything else so every module-level logger call
# made during application construction below is already covered.
setup_logging()

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
    # Middleware. Starlette wraps these so the LAST one added runs
    # OUTERMOST (first on the way in, last on the way out) - so
    # setup_request_id_middleware must be added AFTER
    # setup_logging_middleware for the request_id contextvar to still
    # be set when the logging middleware's own post-request log line
    # runs (it resets the var in a `finally` right after its own
    # call_next returns, which would otherwise happen before an
    # outer/earlier-added logging middleware gets to log).
    setup_cors(application)
    setup_logging_middleware(application)
    setup_request_id_middleware(application)
    setup_metrics_middleware(application)
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
        "metrics": "/metrics",
    }

@app.get("/metrics", tags=["Observability"], include_in_schema=False)
async def metrics(db: Session = Depends(get_db)):
    """
    Prometheus scrape endpoint.

    Intentionally unversioned/root-level (matching standard Prometheus
    scrape conventions) and separate from /api/v1/health. This
    endpoint should not be publicly exposed over the internet - scrape
    it from inside the deployment network only (see
    deployment/nginx/nginx.conf, which does not proxy it, and
    monitoring/prometheus/prometheus.yml).
    """
    update_processing_jobs_gauge(db)
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)