import logging

from app.pipelines.video_pipeline import VideoPipelineService
from app.services.processing_job import ProcessingJobService
from app.services.video import VideoService


logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """
    Top-level orchestration for a single video processing run.

    Owns the ProcessingJob lifecycle (atomic claim, complete, fail)
    and the Video status transitions around it. The actual stage work
    (transcription, summary, embedding, translation, quiz) is fully
    delegated to VideoPipelineService, which is reused as-is.
    """

    def __init__(
        self,
        processing_job_service: ProcessingJobService,
        video_service: VideoService,
        video_pipeline: VideoPipelineService,
    ):
        self.processing_job_service = processing_job_service
        self.video_service = video_service
        self.video_pipeline = video_pipeline

    def run(
        self,
        job_id: int,
        video_id: int,
        file_path: str,
    ) -> None:
        """
        Run the processing pipeline for one job/video.

        Safe to call more than once for the same job_id (e.g. Celery
        task redelivery/retry): only the call that wins the PENDING
        -> RUNNING claim actually runs VideoPipelineService, every
        other call is a no-op.
        """

        claimed = self.processing_job_service.start_if_pending(
            job_id,
        )

        if claimed is None:
            logger.warning(
                "Processing job %s could not be claimed (not "
                "PENDING anymore); skipping duplicate run. This is "
                "expected on Celery task redelivery/retry.",
                job_id,
            )
            return

        logger.info(
            "Processing job %s claimed for video %s.",
            job_id,
            video_id,
        )

        self.video_service.update_status(
            video_id=video_id,
            status="processing",
        )

        try:
            self.video_pipeline.process(
                job_id=job_id,
                video_id=video_id,
                file_path=file_path,
            )
        except Exception as error:
            logger.exception(
                "Processing pipeline failed. job_id=%s video_id=%s",
                job_id,
                video_id,
            )

            self.processing_job_service.fail_job(
                job_id=job_id,
                error=str(error),
            )

            self.video_service.update_status(
                video_id=video_id,
                status="failed",
            )

            raise

        self.processing_job_service.complete_job(
            job_id,
        )
