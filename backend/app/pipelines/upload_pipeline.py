import logging

from app.services.processing_job import ProcessingJobService
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
    ):
        self.processing_job_service = (
            processing_job_service
        )
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

        process_video.delay(
            job.id,
            video_id,
            video_path,
        )
        return job