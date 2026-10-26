import logging
import threading

from celery.signals import worker_ready


logger = logging.getLogger(__name__)


def recover_stale_jobs(limit: int = 100) -> int:
    """
    Fail every RUNNING job orphaned by a dead worker (heartbeat quiet
    for longer than settings.celery.job_heartbeat_timeout_seconds),
    across all videos, and mark their videos failed so the UI offers
    Retry. Returns how many jobs were recovered.

    Safe with several workers: only jobs whose heartbeat has actually
    stopped are touched, and the staleness check is repeated inside
    the UPDATE (ProcessingJobRepository.mark_interrupted), so a job a
    live worker is still running is never failed.
    """
    from app.api.deps import get_upload_pipeline
    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        pipeline = get_upload_pipeline(db)
        recovered = 0
        for job in pipeline.processing_job_service.get_stale_running_jobs(
            limit=limit,
        ):
            if pipeline.recover_stale_running(job) is not None:
                recovered += 1
        return recovered
    finally:
        db.close()


def _run_sweep() -> None:
    try:
        recovered = recover_stale_jobs()
    except Exception:
        logger.exception("Recovery sweep of orphaned processing jobs failed.")
        return

    if recovered:
        logger.warning(
            "Recovered %s processing job(s) orphaned by a previous worker; "
            "they are now FAILED and can be retried.",
            recovered,
        )


@worker_ready.connect
def _recover_on_worker_ready(**_kwargs) -> None:
    """
    A worker starting up is exactly when jobs orphaned by the previous
    run (container restart, engine crash) can be found - nobody may be
    polling those videos, so don't rely on the on-read path alone.

    Sweeps twice: once now (catches jobs orphaned long ago), and once
    after the heartbeat timeout has elapsed, because a job orphaned by
    the crash that just restarted this worker is usually not yet
    "quiet for long enough" at startup. Failures are logged and never
    stop the worker.
    """
    from app.config.settings import settings

    _run_sweep()

    delay = (
        settings.celery.job_heartbeat_timeout_seconds
        + settings.celery.job_heartbeat_interval_seconds
    )
    timer = threading.Timer(delay, _run_sweep)
    timer.daemon = True
    timer.start()
