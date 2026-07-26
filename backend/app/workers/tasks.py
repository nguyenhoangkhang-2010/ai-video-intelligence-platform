from app.workers.celery_app import celery_app

from app.workers.video_processor import process_video


@celery_app.task(
    name="process_video_task"
)
def process_video_task(
    job_id: int,
    video_id: int,
    video_path: str,
):
    """
    Dispatch video processing pipeline.
    """

    process_video(
        job_id=job_id,
        video_id=video_id,
        file_path=video_path,
    )