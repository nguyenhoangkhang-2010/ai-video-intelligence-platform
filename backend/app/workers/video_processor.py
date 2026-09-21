import logging

from app.database.session import SessionLocal

from app.repositories.video import VideoRepository
from app.services.video import VideoService
from app.pipelines.video_pipeline import VideoPipelineService
from app.pipelines.processing_pipeline import ProcessingPipeline

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

from app.repositories.chapter import ChapterRepository
from app.services.chapter import ChapterService

from app.repositories.flashcard import FlashcardRepository
from app.services.flashcard import FlashcardService

from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task
def process_video(
    job_id: int,
    video_id: int,
    file_path: str,
):
    """
    Celery entry point for video processing.

    Only wires up dependencies for one DB session/request; every
    lifecycle decision (claiming the job, marking it
    running/completed/failed, propagating exceptions) is delegated to
    ProcessingPipeline.
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

        chapter_repository = ChapterRepository(db)
        chapter_service = ChapterService(chapter_repository)

        flashcard_repository = FlashcardRepository(db)
        flashcard_service = FlashcardService(flashcard_repository)

        video_pipeline = VideoPipelineService(
            video_service=video_service,
            transcript_service=transcript_service,
            summary_service=summary_service,
            embedding_service=embedding_service,
            translation_service=translation_service,
            processing_job_service=processing_service,
            quiz_service=quiz_service,
            chapter_service=chapter_service,
            flashcard_service=flashcard_service,
        )

        processing_pipeline = ProcessingPipeline(
            processing_job_service=processing_service,
            video_service=video_service,
            video_pipeline=video_pipeline,
        )

        processing_pipeline.run(
            job_id=job_id,
            video_id=video_id,
            file_path=file_path,
        )

    finally:
        db.close()