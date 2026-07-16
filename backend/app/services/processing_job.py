from app.models.processing_job import ProcessingJob
from app.repositories.processing_job import ProcessingJobRepository


class ProcessingJobService:
    """Service for processing job business logic."""

    def __init__(
        self,
        repository: ProcessingJobRepository,
    ):
        self.repository = repository

    def create_processing_job(
        self,
        video_id: int,
        job_type: str = "transcription",
    ) -> ProcessingJob:
        job = ProcessingJob(
            video_id=video_id,
            job_type=job_type,
            status="PENDING",
        )

        return self.repository.create(job)
    
    def get_jobs_by_video(
        self,
        video_id: int,
    ):
        """
        Get all processing jobs of a video.
        """
        return self.repository.get_by_video_id(
            video_id=video_id,
        )