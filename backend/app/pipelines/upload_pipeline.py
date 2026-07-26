from app.services.processing_job import ProcessingJobService
from app.workers.tasks import process_video_task


class UploadPipeline:
    """
    Handle video upload workflow.
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
        process_video_task.delay(
            job.id,
            video_id,
            video_path,
        )
        return job