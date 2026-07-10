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