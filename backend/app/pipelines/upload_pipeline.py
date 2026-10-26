import logging

from app.config.settings import VIDEO_UPLOAD_DIR
from app.models.processing_job import ProcessingJob
from app.services.processing_job import ProcessingJobService
from app.services.video import VideoService
from app.workers.video_processor import process_video


logger = logging.getLogger(__name__)


class UploadPipeline:
    """
    Canonical orchestration for kicking off processing after a video
    is uploaded: create its ProcessingJob and dispatch the canonical
    Celery task.
    """
    def __init__(
        self,
        processing_job_service: ProcessingJobService,
        video_service: VideoService,
    ):
        self.processing_job_service = (
            processing_job_service
        )
        self.video_service = video_service

    def process(
        self,
        video_id: int,
        video_path: str,
    ):
        job = (
            self.processing_job_service
            .create_processing_job(
                video_id=video_id,
                job_type="transcription",
            )
        )

        logger.info(
            "Dispatching processing job %s for video %s.",
            job.id,
            video_id,
        )

        try:
            process_video.delay(
                job.id,
                video_id,
                video_path,
            )
        except Exception as error:
            # The job row is already committed - if .delay() itself
            # raises (broker unreachable, serialization error), that
            # row would otherwise stay PENDING forever with no task
            # behind it (the exact dual-write gap that left jobs 5/13
            # orphaned). Mark it FAILED immediately instead of
            # silently leaving it stuck - this is a terminal,
            # observable state the existing UI already renders
            # ("Processing failed"), rather than a crash of the
            # upload request itself (the file is already saved and
            # the Video row already exists; only its processing
            # failed to start).
            logger.exception(
                "Failed to dispatch processing job %s for video %s.",
                job.id,
                video_id,
            )
            self.processing_job_service.fail_job(
                job_id=job.id,
                error=f"Processing could not be started: {error}",
            )
            self.video_service.update_status(
                video_id=video_id,
                status="failed",
            )
            return job

        return job

    def retry_job(
        self,
        job: ProcessingJob,
    ) -> ProcessingJob:
        """
        Re-dispatch a job that ProcessingJobService.claim_for_retry
        has already atomically transitioned FAILED -> PENDING (see
        the retry endpoint in app.api.v1.endpoints.processing_jobs -
        the only caller). This makes the manual-retry path functional
        rather than a no-op: before this, nothing ever moved a job
        out of FAILED, so VideoPipelineService's existing per-stage
        resume logic (skip COMPLETED stages, retry FAILED/incomplete
        ones) was correct but structurally unreachable once a job
        had failed once.

        Mirrors process()'s own guarded-dispatch behavior exactly: a
        .delay() failure here marks the job FAILED again immediately
        (distinct, observable, never left silently PENDING) rather
        than letting the request crash.
        """
        video = self.video_service.get_video_by_id(job.video_id)

        if video is None:
            return self.processing_job_service.fail_job(
                job.id,
                error=(
                    "Processing could not be started: the video no "
                    "longer exists."
                ),
            )

        video_path = str(VIDEO_UPLOAD_DIR / video.filename)

        try:
            process_video.delay(
                job.id,
                job.video_id,
                video_path,
            )
        except Exception as error:
            logger.exception(
                "Failed to dispatch retry for processing job %s "
                "(video %s).",
                job.id,
                job.video_id,
            )
            self.processing_job_service.fail_job(
                job_id=job.id,
                error=f"Processing could not be started: {error}",
            )
            self.video_service.update_status(
                video_id=job.video_id,
                status="failed",
            )
            return job

        return job

    def reconcile_orphaned_jobs(
        self,
        video_id: int,
    ) -> None:
        """
        Self-healing for UploadPipeline.process's dual-write gap:
        finds any PENDING job for this video whose dispatch never
        arrived (see ProcessingJobService.get_orphaned_pending_jobs)
        and re-attempts dispatch, bounded by
        settings.celery.max_dispatch_attempts. Called opportunistically
        from the processing-jobs read path
        (app.api.v1.endpoints.videos.get_processing_jobs) rather than
        on a schedule - there is no periodic task runner (Celery
        beat) in this project's current infrastructure, and adding
        one solely for this would be exactly the kind of
        undemonstrated-need infra addition to avoid; the frontend
        already polls this exact endpoint while a video is
        processing, which is what actually needs this job unstuck.

        A video nobody is actively viewing (e.g. the two historical
        orphaned jobs this gap left behind) is not reconciled by
        this path - see scripts/reconcile_processing_jobs.py for an
        operator-triggered sweep across every video.
        """
        orphaned = (
            self.processing_job_service.get_orphaned_pending_jobs(
                video_id=video_id,
            )
        )

        for job in orphaned:
            self._reconcile_one(job)

    def _reconcile_one(
        self,
        job: ProcessingJob,
    ) -> None:
        video = self.video_service.get_video_by_id(job.video_id)

        if video is None:
            # Video was deleted after this job was created - nothing
            # to reprocess.
            self.processing_job_service.fail_job(
                job.id,
                error=(
                    "Processing could not be started: the video no "
                    "longer exists."
                ),
            )
            return

        video_path = str(VIDEO_UPLOAD_DIR / video.filename)

        logger.warning(
            "Job %s for video %s looks orphaned (PENDING, never "
            "started, created over the dispatch grace period ago); "
            "re-attempting dispatch (attempt %s).",
            job.id,
            job.video_id,
            job.dispatch_attempts + 1,
        )

        self.processing_job_service.reconcile_orphaned_dispatch(
            job,
            dispatch=lambda: process_video.delay(
                job.id,
                job.video_id,
                video_path,
            ),
        )