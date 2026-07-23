from app.database.session import SessionLocal

from app.repositories.video import VideoRepository
from app.services.video import VideoService
from app.pipelines.video_pipeline import VideoPipelineService

from app.repositories.processing_job import ProcessingJobRepository
from app.services.processing_job import ProcessingJobService

from app.repositories.transcript import TranscriptRepository
from app.services.transcript import TranscriptService
from app.schemas.transcript import TranscriptCreate

def process_video(
    job_id: int,
    video_id: int,
    file_path: str,
):
    """
    Background worker for processing uploaded videos.
    """
    db = SessionLocal()

    try:
        video_repository = VideoRepository(db)
        video_service = VideoService(video_repository)

        processing_repository = ProcessingJobRepository(db)
        processing_service = ProcessingJobService(processing_repository)
        
        transcript_repository = TranscriptRepository(db)
        transcript_service = TranscriptService(transcript_repository)

        pipeline = VideoPipelineService(video_service)
        
        transcript = pipeline.process(
            video_id=video_id,
            file_path=file_path,
        )
        
        transcript_service.create_transcript(
            TranscriptCreate(
                video_id=video_id,
                language=transcript["language"],
                text=transcript["text"],
            )
        )
        
        processing_service.complete_job(job_id)

    except Exception as e:
        processing_service.fail_job(
            job_id=job_id,
            error=str(e),
        )
        raise

    finally:
        db.close()