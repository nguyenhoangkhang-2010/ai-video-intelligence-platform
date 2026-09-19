from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.session import get_db

from app.repositories.video import VideoRepository
from app.services.video import VideoService

from app.repositories.processing_job import ProcessingJobRepository
from app.services.processing_job import ProcessingJobService

from app.repositories.transcript import TranscriptRepository
from app.services.transcript import TranscriptService

from app.repositories.quiz import QuizRepository
from app.services.quiz import QuizService

from app.repositories.summary import SummaryRepository
from app.services.summary import SummaryService

from app.repositories.translation import TranslationRepository
from app.services.translation import TranslationService

from app.repositories.embedding import EmbeddingRepository
from app.services.embedding import EmbeddingService
from app.services.semantic_search import SemanticSearchService
from app.pipelines.rag_pipeline import RAGPipeline
from app.pipelines.upload_pipeline import UploadPipeline

def get_video_service(
    db: Session = Depends(get_db),
) -> VideoService:
    """
    Dependency that provides a VideoService instance.
    """
    repository = VideoRepository(db)

    return VideoService(repository)

def get_processing_job_service(
    db: Session = Depends(get_db),
) -> ProcessingJobService:
    repository = ProcessingJobRepository(db)
    return ProcessingJobService(repository)

def get_transcript_service(
    db: Session = Depends(get_db),
) -> TranscriptService:
    repository = TranscriptRepository(db)
    return TranscriptService(repository)

def get_quiz_service(
    db: Session = Depends(get_db),
) -> QuizService:
    repository = QuizRepository(db)
    return QuizService(repository)

def get_summary_service(
    db: Session = Depends(get_db),
) -> SummaryService:
    repository = SummaryRepository(db)
    return SummaryService(repository)

def get_translation_service(
    db: Session = Depends(get_db),
) -> TranslationService:
    repository = TranslationRepository(db)
    return TranslationService(repository)

def get_rag_pipeline(
    db: Session = Depends(get_db),
) -> RAGPipeline:
    """
    Dependency that provides a RAGPipeline instance.
    """
    embedding_repository = EmbeddingRepository(db)
    embedding_service = EmbeddingService(embedding_repository)

    semantic_search_service = SemanticSearchService(
        embedding_repository=embedding_repository,
    )

    return RAGPipeline(
        semantic_search_service=semantic_search_service,
        embedding_service=embedding_service,
    )

def get_upload_pipeline(
    db: Session = Depends(get_db),
) -> UploadPipeline:
    """
    Dependency that provides an UploadPipeline instance.
    """
    repository = ProcessingJobRepository(db)
    processing_job_service = ProcessingJobService(repository)

    return UploadPipeline(
        processing_job_service=processing_job_service,
    )