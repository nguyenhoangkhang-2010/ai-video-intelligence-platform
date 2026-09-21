import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Liveness/readiness probe for Docker Compose healthchecks and CI.

    Checks database connectivity (the one dependency every request
    path needs) with a trivial query - not a substitute for full
    monitoring (see Phase 13 for Prometheus/Grafana), just enough for
    infrastructure to know whether this instance is ready to serve
    traffic.
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.warning("Health check: database is unreachable.", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unreachable"},
        )

    return {"status": "ok", "database": "connected"}
