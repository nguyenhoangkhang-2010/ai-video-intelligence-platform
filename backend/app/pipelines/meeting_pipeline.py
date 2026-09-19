import logging

from app.pipelines.processing_pipeline import ProcessingPipeline


logger = logging.getLogger(__name__)


class MeetingPipeline:
    """
    Orchestration entry point for meeting-flavored video processing.

    There is currently no distinct Meeting domain in this codebase:
    no Meeting model/table exists, and the AI components that would
    make meeting processing differ from generic video processing
    (speaker diarization, structured knowledge/action-item
    extraction) are unimplemented stubs - ai/diarization/ and
    ai/knowledge_graph/ are empty files with no logic. A meeting
    recording is therefore processed identically to any other video
    today, through the existing ProcessingPipeline -> VideoPipelineService
    orchestration. Nothing from that flow is duplicated or
    reimplemented here.

    This class exists as a stable, named entry point so a future
    meeting-specific API/dispatcher has somewhere to call into, and
    so that if/when real meeting-specific stages are added, they have
    an obvious home that does not require touching ProcessingPipeline
    or VideoPipelineService.
    """

    def __init__(
        self,
        processing_pipeline: ProcessingPipeline,
    ):
        self.processing_pipeline = processing_pipeline

    def run(
        self,
        job_id: int,
        video_id: int,
        file_path: str,
    ) -> None:
        """
        Run meeting processing for one job/video.

        Delegates entirely to ProcessingPipeline, which already
        provides idempotent job claiming (safe under Celery
        redelivery/retry), video status transitions, and failure
        handling - none of that is reimplemented here.
        """
        logger.info(
            "Meeting pipeline delegating to ProcessingPipeline for "
            "job %s, video %s.",
            job_id,
            video_id,
        )

        self.processing_pipeline.run(
            job_id=job_id,
            video_id=video_id,
            file_path=file_path,
        )
