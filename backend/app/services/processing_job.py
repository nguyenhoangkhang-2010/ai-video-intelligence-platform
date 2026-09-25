from app.core.exceptions import InvalidJobStatusTransitionError
from app.models.processing_job import ProcessingJob
from app.repositories.processing_job import ProcessingJobRepository

from fastapi import HTTPException
from fastapi import status as http_status

from datetime import datetime, UTC

# Transitions a caller of update_job_status (the only path
# PATCH /processing-jobs/{id} - a client-facing, owner-writable
# endpoint - goes through) may request. Terminal states (COMPLETED,
# FAILED) allow no further transition. Internal pipeline code
# (start_job/complete_job/fail_job/update_progress, driven by the
# Celery worker, not this method) is unaffected - this only
# constrains the one client-writable status path.
_VALID_JOB_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"RUNNING", "FAILED"},
    "RUNNING": {"COMPLETED", "FAILED"},
    "COMPLETED": set(),
    "FAILED": set(),
}

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
        Get all processing jobs, across every user's videos.

        Not ownership-scoped - kept for internal/administrative use
        only. Do not expose this to a regular authenticated user; see
        get_jobs_for_user for the ownership-scoped equivalent used by
        the public API.
        """
        return self.repository.get_all()

    def get_jobs_for_user(
        self,
        user_id: int,
    ) -> list[ProcessingJob]:
        """
        Get all processing jobs belonging to `user_id`'s own videos.
        """
        return self.repository.get_by_owner(
            owner_id=user_id,
        )

    def get_job(
        self,
        job_id: int,
    ) -> ProcessingJob:
        """
        Get processing job by ID.

        Not ownership-scoped - kept for internal/administrative use
        only (e.g. from another service call already scoped by video
        ownership, as in videos.get_processing_jobs). Do not expose
        this to a regular authenticated user directly; see
        get_job_for_user for the ownership-scoped equivalent used by
        the public API.
        """
        job = self.repository.get_by_id(job_id)

        if job is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Processing job not found",
            )

        return job

    def get_job_for_user(
        self,
        job_id: int,
        user_id: int,
    ) -> ProcessingJob:
        """
        Get a single processing job by ID, only if it belongs to one
        of `user_id`'s own videos. Raises 404 (not 403) on a mismatch,
        matching VideoService.get_video's convention of not revealing
        whether a job with that ID exists for someone else.
        """
        job = self.repository.get_by_id_and_owner(
            job_id=job_id,
            owner_id=user_id,
        )

        if job is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
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
        Update processing job status (the client-facing
        PATCH /processing-jobs/{id} path only - see
        _VALID_JOB_STATUS_TRANSITIONS).
        """
        job = self.repository.get_by_id(job_id)

        if job is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Processing job not found",
            )

        allowed_next_statuses = _VALID_JOB_STATUS_TRANSITIONS.get(
            job.status, set(),
        )

        if status not in allowed_next_statuses:
            raise InvalidJobStatusTransitionError(
                f"Cannot transition processing job from "
                f"'{job.status}' to '{status}'."
            )

        job.status = status

        if status == "RUNNING" and job.started_at is None:
            job.started_at = datetime.now(UTC)

        if status == "COMPLETED":
            job.finished_at = datetime.now(UTC)

        if status == "FAILED":
            job.finished_at = datetime.now(UTC)
            job.current_step = "Failed"
            job.progress = 100

        if error_message is not None:
            job.error_message = error_message

        return self.repository.update(job)
    
    def start_if_pending(
        self,
        job_id: int,
    ) -> ProcessingJob | None:
        """
        Atomically claim a PENDING job for processing. Returns None
        if the job could not be claimed (not found, or already
        running/completed/failed) - the caller should treat that as
        "already handled by a concurrent delivery" and skip re-running
        the pipeline, rather than an error. Unlike other methods on
        this service, this intentionally does not raise 404 on a
        miss, since that outcome is expected under Celery task
        redelivery/retry.
        """
        return self.repository.claim_for_running(
            job_id,
        )

    def start_job(
        self,
        job_id: int,
    ) -> ProcessingJob:
        """
        Mark a processing job as RUNNING.
        """
        job = self.repository.get_by_id(job_id)

        if job is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Processing job not found",
            )

        job.status = "RUNNING"
        job.started_at = datetime.now(UTC)

        return self.repository.update(job)
        
    def complete_job(
        self,
        job_id: int,
    ) -> ProcessingJob:
        """
        Mark a processing job as COMPLETED.
        """
        job = self.repository.get_by_id(job_id)

        if job is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Processing job not found",
            )

        job.status = "COMPLETED"
        job.finished_at = datetime.now(UTC)

        return self.repository.update(job)
    
    def fail_job(
        self,
        job_id: int,
        error: str,
    ) -> ProcessingJob:
        """
        Mark a processing job as FAILED.
        """
        job = self.repository.get_by_id(job_id)

        if job is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Processing job not found",
            )

        job.status = "FAILED"
        job.progress = 100
        job.current_step = "Failed"
        job.error_message = error
        job.finished_at = datetime.now(UTC)

        return self.repository.update(job)
    
    def update_progress(
        self,
        job_id: int,
        progress: int,
        current_step: str,
        status: str | None = None,
    ) -> ProcessingJob:
        """
        Update processing progress of a job.
        """

        job = self.repository.get_by_id(job_id)

        if job is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Processing job not found",
            )

        return self.repository.update_progress(
            job=job,
            progress=progress,
            current_step=current_step,
            status=status,
        )