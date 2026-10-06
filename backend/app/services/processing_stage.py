from app.config.settings import settings
from app.models.processing_stage import ProcessingStage
from app.repositories.processing_stage import ProcessingStageRepository


class ProcessingStageService:
    """Service for ProcessingStage lifecycle operations."""

    def __init__(
        self,
        repository: ProcessingStageRepository,
    ):
        self.repository = repository

    def get_by_job_id(
        self,
        processing_job_id: int,
    ) -> list[ProcessingStage]:
        return self.repository.get_by_job_id(
            processing_job_id,
        )

    def get_by_job_id_and_name(
        self,
        processing_job_id: int,
        stage_name: str,
    ) -> ProcessingStage | None:
        return self.repository.get_by_job_id_and_name(
            processing_job_id,
            stage_name,
        )

    def ensure_seeded(
        self,
        processing_job_id: int,
        stage_names: tuple[str, ...],
    ) -> dict[str, ProcessingStage]:
        """
        Idempotently ensure a PENDING row exists for every name in
        `stage_names`. Safe to call on every run (first attempt or
        resume after a crash) - rows that already exist are returned
        untouched, never reset.
        """
        return {
            stage_name: self.repository.create_if_absent(
                processing_job_id,
                stage_name,
            )
            for stage_name in stage_names
        }

    def has_exhausted_retries(
        self,
        stage: ProcessingStage,
    ) -> bool:
        """
        True once a FAILED stage has already used up the same bounded
        retry budget Celery's own task-level autoretry uses
        (settings.celery.task_max_retries) - reused rather than a new,
        separate retry-count setting invented for stages specifically.
        """
        return stage.attempt_count >= settings.celery.task_max_retries

    def try_claim(
        self,
        processing_job_id: int,
        stage_name: str,
    ) -> ProcessingStage | None:
        """
        Attempt to atomically claim this stage for execution. Returns
        None if it could not be claimed (already COMPLETED/SKIPPED,
        or genuinely RUNNING under a still-alive attempt).

        stale_after_seconds = settings.celery.task_time_limit: no
        legitimate single execution of process_video can still be
        alive beyond this many seconds - Celery itself guarantees
        that by killing the worker process at that point - so a
        RUNNING stage older than this is safely known to be
        abandoned, not a race against a still-running attempt.
        """
        return self.repository.claim_for_running(
            processing_job_id,
            stage_name,
            stale_after_seconds=settings.celery.task_time_limit,
        )

    def mark_completed(
        self,
        stage: ProcessingStage,
    ) -> ProcessingStage:
        return self.repository.mark_completed(stage)

    def mark_failed(
        self,
        stage: ProcessingStage,
        error_message: str,
    ) -> ProcessingStage:
        return self.repository.mark_failed(stage, error_message)

    def mark_skipped(
        self,
        stage: ProcessingStage,
    ) -> ProcessingStage:
        return self.repository.mark_skipped(stage)
