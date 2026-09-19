from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.models.processing_job import ProcessingJob
from app.repositories.base import BaseRepository


class ProcessingJobRepository(BaseRepository[ProcessingJob]):
    """Repository for ProcessingJob model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=ProcessingJob,
        )

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[ProcessingJob]:

        return (
            self.db.query(ProcessingJob)
            .filter(ProcessingJob.video_id == video_id)
            .all()
        )

    def get_by_status(
        self,
        status: str,
    ) -> list[ProcessingJob]:

        return (
            self.db.query(ProcessingJob)
            .filter(ProcessingJob.status == status)
            .all()
        )

    def get_by_job_type(
        self,
        job_type: str,
    ) -> list[ProcessingJob]:

        return (
            self.db.query(ProcessingJob)
            .filter(ProcessingJob.job_type == job_type)
            .all()
        )
    
    def update(
        self,
        job: ProcessingJob,
    ) -> ProcessingJob:
        self.db.commit()
        self.db.refresh(job)
        return job

    def claim_for_running(
        self,
        job_id: int,
    ) -> ProcessingJob | None:
        """
        Atomically transition a job PENDING -> RUNNING and stamp
        started_at, but only if it is still PENDING.

        This is a conditional UPDATE ... WHERE status = 'PENDING'. If
        two deliveries of the same Celery task race to claim the same
        job, the database's row-level locking on the UPDATE ensures
        only one of them can ever match the row and win; the other
        sees 0 updated rows and gets None back, signalling "already
        claimed elsewhere, skip".
        """

        updated_rows = (
            self.db.query(ProcessingJob)
            .filter(
                ProcessingJob.id == job_id,
                ProcessingJob.status == "PENDING",
            )
            .update(
                {
                    ProcessingJob.status: "RUNNING",
                    ProcessingJob.started_at: datetime.now(UTC),
                },
                synchronize_session=False,
            )
        )

        self.db.commit()

        if updated_rows == 0:
            return None

        return self.get_by_id(job_id)
    
    def update_progress(
        self,
        job: ProcessingJob,
        progress: int,
        current_step: str,
        status: str | None = None,
    ) -> ProcessingJob:
        job.progress = progress
        job.current_step = current_step

        if status is not None:
            job.status = status

        self.db.commit()
        self.db.refresh(job)

        return job
    
    def get_by_id(
        self,
        job_id:int
    ):
        return (
            self.db.query(ProcessingJob)
            .filter(
                ProcessingJob.id == job_id
            )
            .first()
        )