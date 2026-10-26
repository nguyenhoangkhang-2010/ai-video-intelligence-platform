import logging
import threading
from collections.abc import Callable
from types import TracebackType

from app.config.settings import settings


logger = logging.getLogger(__name__)


class JobHeartbeat:
    """
    Keeps a RUNNING job's heartbeat_at fresh from a background thread
    for as long as the pipeline is working on it.

    Long stages (transcription, embedding) can run for minutes without
    a progress update, so progress writes alone can't prove the worker
    is alive. This thread proves it independently: if the worker
    process dies (container restart, engine crash, OOM kill), the
    thread dies with it, heartbeat_at stops moving, and the job becomes
    recoverable once settings.celery.job_heartbeat_timeout_seconds has
    passed (see ProcessingJobService.reconcile_stale_running).

    `touch` is a zero-arg callable that refreshes the heartbeat and
    returns False once the job is no longer RUNNING - it must use its
    own database session, since it runs on another thread than the
    pipeline. A failing touch (e.g. the database briefly unreachable)
    is logged and retried on the next tick, never raised into the
    pipeline.

    Use as a context manager around the work:

        with JobHeartbeat(touch, job_id=42):
            run_pipeline()
    """

    def __init__(
        self,
        touch: Callable[[], bool],
        job_id: int,
        interval_seconds: float | None = None,
    ):
        self._touch = touch
        self._job_id = job_id
        self._interval = (
            interval_seconds
            if interval_seconds is not None
            else settings.celery.job_heartbeat_interval_seconds
        )
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name=f"job-heartbeat-{job_id}",
            daemon=True,
        )

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            try:
                still_running = self._touch()
            except Exception:
                logger.warning(
                    "Heartbeat for processing job %s failed; will retry.",
                    self._job_id,
                    exc_info=True,
                )
                continue

            if not still_running:
                return

    def __enter__(self) -> "JobHeartbeat":
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._stop.set()
        self._thread.join(timeout=self._interval + 5)


def database_heartbeat(job_id: int) -> JobHeartbeat:
    """
    JobHeartbeat whose touches each use a short-lived session of their
    own (never the pipeline's session, which isn't thread-safe).
    """
    from app.database.session import SessionLocal
    from app.repositories.processing_job import ProcessingJobRepository

    def touch() -> bool:
        db = SessionLocal()
        try:
            return ProcessingJobRepository(db).touch_heartbeat(job_id)
        finally:
            db.close()

    return JobHeartbeat(touch, job_id=job_id)
