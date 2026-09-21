"""
Prometheus metrics for the FastAPI process.

Kept deliberately small: HTTP request count + latency (the two
metrics every HTTP service should expose) plus one domain gauge
(processing_jobs_active) that's cheap to compute and directly useful
for an operator watching the video processing backlog.

Celery worker-side task metrics live in a different process (and
therefore a different Prometheus client registry) - see
app.workers.metrics for those; they are exposed on a separate port,
not through this module's /metrics endpoint.

Route path *templates* (e.g. "/api/v1/videos/{video_id}"), not the
resolved request path, are used as label values - using the resolved
path would create one time series per distinct video/job/etc. id
(unbounded cardinality), which is a well-known Prometheus pitfall.
"""
import logging
import time

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.processing_job import ProcessingJob

logger = logging.getLogger(__name__)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests received.",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)

PROCESSING_JOBS_ACTIVE = Gauge(
    "processing_jobs_active",
    "Number of processing jobs currently PENDING or RUNNING.",
)


def _route_path_template(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


def setup_metrics_middleware(app: FastAPI) -> None:
    """
    Registers HTTP request count/latency instrumentation. A no-op if
    metrics are disabled (settings.metrics.enabled / METRICS_ENABLED).
    """
    if not settings.metrics.enabled:
        return

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        duration = time.perf_counter() - start
        path = _route_path_template(request)

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=path,
            status_code=response.status_code,
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            path=path,
        ).observe(duration)

        return response


def update_processing_jobs_gauge(db: Session) -> None:
    """
    Refresh PROCESSING_JOBS_ACTIVE from the database. Computed at
    scrape time (a single indexed COUNT query) rather than
    incrementally tracked across every service call site, so no
    existing ProcessingJob service/repository code needs to change to
    keep this metric accurate.

    A database error here must not take down the whole /metrics
    endpoint (that would hide the very outage an operator most needs
    metrics for) - on failure, the gauge simply keeps its last known
    value and the rest of /metrics (HTTP request metrics, which need
    no DB access) is still served.
    """
    try:
        active_count = (
            db.query(func.count(ProcessingJob.id))
            .filter(ProcessingJob.status.in_(["PENDING", "RUNNING"]))
            .scalar()
        )
    except Exception:
        logger.warning(
            "Failed to refresh processing_jobs_active gauge; keeping "
            "last known value.",
            exc_info=True,
        )
        return

    PROCESSING_JOBS_ACTIVE.set(active_count or 0)


def render_metrics() -> tuple[bytes, str]:
    """Return (body, content_type) for the /metrics endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST
