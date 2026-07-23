from app.workers.celery_app import celery_app

from app.database.session import SessionLocal

from app.services.processing_job import ProcessingJobService
from app.repositories.processing_job import ProcessingJobRepository

from app.workers.video_processor import process_video


@celery_app.task(
    name="process_video_task"
)
def process_video_task(
    job_id: int,
    video_id: int,
    video_path: str,
):

    db = SessionLocal()
    repository = ProcessingJobRepository(
        db=db,
    )
    
    job_service = ProcessingJobService(
        repository=repository,
    )
    try:
        # RUNNING
        job_service.start_job(
            job_id,
        )
        # Whisper pipeline
        process_video(
            video_id=video_id,
            video_path=video_path,
        )
        # COMPLETED
        job_service.complete_job(
            job_id,
        )
    except Exception as e:
        job_service.fail_job(
            job_id,
            str(e),
        )
        raise e
    finally:
        db.close()