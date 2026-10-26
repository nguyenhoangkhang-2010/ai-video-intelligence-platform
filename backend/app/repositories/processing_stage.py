from datetime import datetime, timedelta, UTC

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.processing_stage import ProcessingStage
from app.repositories.base import BaseRepository


class ProcessingStageRepository(BaseRepository[ProcessingStage]):
    """Repository for ProcessingStage model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=ProcessingStage,
        )

    def get_by_job_id(
        self,
        processing_job_id: int,
    ) -> list[ProcessingStage]:

        return (
            self.db.query(ProcessingStage)
            .filter(ProcessingStage.processing_job_id == processing_job_id)
            .all()
        )

    def get_by_job_id_and_name(
        self,
        processing_job_id: int,
        stage_name: str,
    ) -> ProcessingStage | None:

        return (
            self.db.query(ProcessingStage)
            .filter(
                ProcessingStage.processing_job_id == processing_job_id,
                ProcessingStage.stage_name == stage_name,
            )
            .first()
        )

    def create_if_absent(
        self,
        processing_job_id: int,
        stage_name: str,
    ) -> ProcessingStage:
        """
        Idempotently ensure a PENDING row exists for this (job, stage)
        pair. Check-then-insert, backed by the real
        UNIQUE(processing_job_id, stage_name) constraint as the
        correctness guarantee under a genuine race (two near-
        simultaneous resumes both seeding the same job's stage rows):
        the losing insert's IntegrityError is caught and the winner's
        row is re-fetched, rather than raising. This mirrors the
        existing check-then-insert-with-fallback convention already
        used by e.g. SummaryService.create_summary - it is the row-
        seeding path, not the atomic claim (see claim_for_running for
        that).
        """
        existing = self.get_by_job_id_and_name(
            processing_job_id,
            stage_name,
        )

        if existing is not None:
            return existing

        stage = ProcessingStage(
            processing_job_id=processing_job_id,
            stage_name=stage_name,
            status="PENDING",
        )

        try:
            self.db.add(stage)
            self.db.commit()
            self.db.refresh(stage)
            return stage
        except IntegrityError:
            self.db.rollback()
            return self.get_by_job_id_and_name(
                processing_job_id,
                stage_name,
            )

    def claim_for_running(
        self,
        processing_job_id: int,
        stage_name: str,
        stale_after_seconds: int,
    ) -> ProcessingStage | None:
        """
        Atomically claim a stage for execution: PENDING -> RUNNING,
        FAILED -> RUNNING (a retry), or a stale RUNNING row (started
        longer than `stale_after_seconds` ago, meaning the worker that
        claimed it is presumed crashed) -> RUNNING again.

        Single conditional UPDATE, exactly mirroring
        ProcessingJobRepository.claim_for_running's shape: if two
        callers race for the same (job, stage), the database's row-
        level locking on the UPDATE ensures only one can ever match
        and win; the other sees 0 updated rows and gets None back.
        attempt_count is incremented by the database itself
        (`attempt_count + 1` in the SET clause), not read-then-
        written in Python, so the increment is part of the same
        atomic statement.
        """
        now = datetime.now(UTC)
        stale_cutoff = now - timedelta(seconds=stale_after_seconds)

        updated_rows = (
            self.db.query(ProcessingStage)
            .filter(
                ProcessingStage.processing_job_id == processing_job_id,
                ProcessingStage.stage_name == stage_name,
                or_(
                    ProcessingStage.status.in_(("PENDING", "FAILED")),
                    and_(
                        ProcessingStage.status == "RUNNING",
                        ProcessingStage.started_at < stale_cutoff,
                    ),
                ),
            )
            .update(
                {
                    ProcessingStage.status: "RUNNING",
                    ProcessingStage.started_at: now,
                    ProcessingStage.finished_at: None,
                    ProcessingStage.error_message: None,
                    ProcessingStage.attempt_count: ProcessingStage.attempt_count + 1,
                },
                synchronize_session=False,
            )
        )

        self.db.commit()

        if updated_rows == 0:
            return None

        return self.get_by_job_id_and_name(
            processing_job_id,
            stage_name,
        )

    def mark_completed(
        self,
        stage: ProcessingStage,
    ) -> ProcessingStage:
        stage.status = "COMPLETED"
        stage.finished_at = datetime.now(UTC)
        stage.error_message = None

        self.db.commit()
        self.db.refresh(stage)

        return stage

    def mark_failed(
        self,
        stage: ProcessingStage,
        error_message: str,
    ) -> ProcessingStage:
        stage.status = "FAILED"
        stage.finished_at = datetime.now(UTC)
        stage.error_message = error_message

        self.db.commit()
        self.db.refresh(stage)

        return stage

    def mark_skipped(
        self,
        stage: ProcessingStage,
    ) -> ProcessingStage:
        stage.status = "SKIPPED"
        stage.finished_at = datetime.now(UTC)
        stage.error_message = None

        self.db.commit()
        self.db.refresh(stage)

        return stage
