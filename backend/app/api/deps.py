import logging
from functools import lru_cache

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
from app.config.settings import settings

from ai.reranking.reranker import Reranker
from ai.retrieval.dense_retriever import DenseRetriever
from ai.retrieval.hybrid_search import HybridRetriever
from ai.retrieval.retriever import Retriever
from ai.retrieval.sparse_retriever import SparseRetriever

from app.repositories.chapter import ChapterRepository
from app.services.chapter import ChapterService

from app.repositories.flashcard import FlashcardRepository
from app.services.flashcard import FlashcardService

from app.storage.base import StorageBackend
from app.storage.factory import get_storage_backend as _get_storage_backend

logger = logging.getLogger(__name__)


@lru_cache
def _get_cross_encoder_reranker() -> Reranker | None:
    """
    Load the cross-encoder reranker once per process and reuse it for
    every RAG request (loading a real ML model per-request would be
    far too slow). Cached with lru_cache instead of loaded at import
    time, so the (possibly slow/network-dependent) model load only
    happens on first actual use, not on every process/test import.

    Graceful fallback: if the model can't be loaded (not cached
    locally, no network access, etc.), this logs a warning and caches
    `None` - callers treat that as "no reranker available" and RAG
    continues to work via dense/hybrid retrieval alone, exactly as it
    did before reranking existed. The failure is never allowed to
    break a RAG request.
    """
    try:
        from ai.reranking.cross_encoder import CrossEncoderReranker

        return CrossEncoderReranker()
    except Exception:
        logger.warning(
            "Cross-encoder reranker could not be loaded; RAG will "
            "run without reranking.",
            exc_info=True,
        )
        return None


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

def get_embedding_service(
    db: Session = Depends(get_db),
) -> EmbeddingService:
    repository = EmbeddingRepository(db)
    return EmbeddingService(repository)

def get_rag_pipeline(
    db: Session = Depends(get_db),
) -> RAGPipeline:
    """
    Dependency that provides a RAGPipeline instance.

    Retrieval: dense (FAISS) alone by default matched the original
    behavior, but this project's own ai/retrieval/hybrid_search.py
    (BM25 + dense fused via RRF) and ai/reranking/cross_encoder.py
    were fully implemented and unit-tested without ever being wired
    in here - see docs/api/rest_api.md. Both are now used when their
    settings.retrieval flags are enabled (on by default):

        dense + sparse (BM25) -> HybridRetriever (RRF)
            -> RetrievalPipeline -> optional CrossEncoderReranker

    The RAGPipeline/RAGResult API contract (four status values,
    SearchResult shape) is unchanged - only which Retriever/Reranker
    RetrievalPipeline is built with changes here.
    """
    embedding_repository = EmbeddingRepository(db)
    embedding_service = EmbeddingService(embedding_repository)

    semantic_search_service = SemanticSearchService(
        embedding_repository=embedding_repository,
    )

    retriever: Retriever = DenseRetriever(
        semantic_search_service=semantic_search_service,
    )

    if settings.retrieval.hybrid_enabled:
        retriever = HybridRetriever(
            retrievers=[
                retriever,
                SparseRetriever(
                    embedding_repository=embedding_repository,
                ),
            ],
        )

    reranker = (
        _get_cross_encoder_reranker()
        if settings.retrieval.reranking_enabled
        else None
    )

    return RAGPipeline(
        semantic_search_service=semantic_search_service,
        embedding_service=embedding_service,
        retriever=retriever,
        reranker=reranker,
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

def get_chapter_service(
    db: Session = Depends(get_db),
) -> ChapterService:
    repository = ChapterRepository(db)
    return ChapterService(repository)

def get_flashcard_service(
    db: Session = Depends(get_db),
) -> FlashcardService:
    repository = FlashcardRepository(db)
    return FlashcardService(repository)

def get_storage_backend() -> StorageBackend:
    """
    Dependency that provides the configured StorageBackend (local or
    S3/MinIO, per settings.storage.backend) - reused as-is from
    app.storage.factory, not reimplemented here.
    """
    return _get_storage_backend()