from app.models.processing_job import ProcessingJob
from app.repositories.processing_job import ProcessingJobRepository

from fastapi import HTTPException
from fastapi import status

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
    ) -> list[ProcessingJob]:
        """
        Get all processing jobs of a video.
        """
        return self.repository.get_by_video_id(
            video_id=video_id,
        )
        
    def get_all_jobs(
        self,
    ) -> list[ProcessingJob]:
        """
        Get all processing jobs.
        """
        return self.repository.get_all()
    
    def get_job(
        self,
        job_id: int,
    ) -> ProcessingJob:
        """
        Get processing job by ID.
        """
        job = self.repository.get_by_id(job_id)

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing job not found",
            )

        return job
    
    def update_job_status(
        self,
        job_id: int,
        status: str,
        error_message: str | None = None,
    ) -> ProcessingJob:
        """
        Update processing job status.
        """
        job = self.repository.get_by_id(job_id)

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing job not found",
            )

        job.status = status

        if error_message is not None:
            job.error_message = error_message

        return self.repository.update(job)