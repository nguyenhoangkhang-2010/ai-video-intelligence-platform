import logging

from app.database.session import SessionLocal

from app.repositories.video import VideoRepository
from app.services.video import VideoService
from app.pipelines.video_pipeline import VideoPipelineService

from app.repositories.processing_job import ProcessingJobRepository
from app.services.processing_job import ProcessingJobService

from app.repositories.transcript import TranscriptRepository
from app.services.transcript import TranscriptService

from app.repositories.summary import SummaryRepository
from app.services.summary import SummaryService

from app.repositories.embedding import EmbeddingRepository
from app.services.embedding import EmbeddingService

from app.repositories.translation import TranslationRepository
from app.services.translation import TranslationService

from app.repositories.quiz import QuizRepository
from app.services.quiz import QuizService

from app.core.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task
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
        
        summary_repository = SummaryRepository(db)
        summary_service = SummaryService(summary_repository)

        embedding_repository = EmbeddingRepository(db)
        embedding_service = EmbeddingService(embedding_repository)
        
        translation_repository = TranslationRepository(db)
        translation_service = TranslationService(translation_repository)
        
        quiz_repository = QuizRepository(db)
        quiz_service = QuizService(quiz_repository)

        pipeline = VideoPipelineService(
            video_service=video_service,
            transcript_service=transcript_service,
            summary_service=summary_service,
            embedding_service=embedding_service,
            translation_service=translation_service,
            processing_job_service=processing_service,
            quiz_service=quiz_service,
        )
        
        processing_service.start_job(job_id)
        
        pipeline.process(
            job_id=job_id,
            video_id=video_id,
            file_path=file_path,
        )
        
        processing_service.complete_job(job_id)

    except Exception as e:
        logger.exception(
            "Video processing failed. job_id=%s",
            job_id,
        )
        
        processing_service.fail_job(
            job_id=job_id,
            error=str(e),
        )
        raise

    finally:
        db.close()