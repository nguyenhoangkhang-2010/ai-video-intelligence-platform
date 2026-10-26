import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


def _check_database(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.warning("Health check: database is unreachable.", exc_info=True)
        return False


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Combined liveness+readiness probe, kept for backward compatibility
    with existing Docker/Compose healthchecks and nginx config that
    already reference this exact path. Equivalent to /health/ready -
    see that endpoint's docstring. Prefer /health/live and
    /health/ready directly for new integrations that want the
    distinction.
    """
    if not _check_database(db):
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unreachable"},
        )

    return {"status": "ok", "database": "connected"}


@router.get("/health/live")
def liveness_check():
    """
    Liveness probe: is the process itself alive and able to handle a
    request at all? Deliberately checks nothing else (no database, no
    Ollama, no AI models) - a slow/unreachable dependency must never
    make this fail, or an orchestrator would kill and restart a
    perfectly healthy process for someone else's outage.
    """
    return {"status": "ok"}


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe: can this instance actually serve requests right
    now? Checks database connectivity - the one dependency every
    request path needs - with a trivial query. Deliberately does NOT
    check optional/best-effort external services (e.g. Ollama):
    losing LLM-backed features temporarily should not pull a healthy
    API instance out of rotation.
    """
    if not _check_database(db):
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unreachable"},
        )

    return {"status": "ok", "database": "connected"}
