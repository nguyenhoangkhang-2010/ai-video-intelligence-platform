import logging

from fastapi import Depends
from sqlalchemy.orm import Session

from fastapi import APIRouter

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.config.settings import settings
from app.core.rate_limit import rate_limit
from app.database.session import get_db
from app.repositories.embedding import EmbeddingRepository

from app.api.deps import get_rag_pipeline
from app.api.deps import get_video_service

from app.pipelines.rag_pipeline import RAGPipeline
from app.services.video import VideoService

from app.schemas.rag import RAGResult
from app.schemas.search import SearchRequest
from app.schemas.search import SemanticSearchResponse
from app.services.semantic_search import SemanticSearchService


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.post(
    "/videos/{video_id}",
    response_model=SemanticSearchResponse,
    dependencies=[Depends(rate_limit("search", settings.rate_limit.search_limit, 60))],
)
def search_video(
    video_id: int,
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    db: Session = Depends(get_db),
):
    """
    Semantic search inside video content.

    Ownership-checked exactly like the RAG endpoint below - this
    previously had no authentication/ownership check at all, letting
    any caller search any video's content by guessing an id.
    """

    # check ownership
    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    logger.info(
        "Searching video %s with query: %s",
        video_id,
        request.query,
    )

    embedding_repository = EmbeddingRepository(
        db=db,
    )

    service = SemanticSearchService(
        embedding_repository=embedding_repository,
    )

    results = service.search(
        video_id=video_id,
        query=request.query,
        top_k=request.top_k,
    )

    return {
        "video_id": video_id,
        "query": request.query,
        "results": results,
    }


@router.post(
    "/videos/{video_id}/rag",
    response_model=RAGResult,
    dependencies=[Depends(rate_limit("rag", settings.rate_limit.search_limit, 60))],
)
def ask_video(
    video_id: int,
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
):
    """
    Ask a question grounded in a video's transcript content, using
    retrieval-augmented generation scoped to that video only.
    """

    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    logger.info(
        "RAG query for video %s: %s",
        video_id,
        request.query,
    )

    return rag_pipeline.ask(
        video_id=video_id,
        query=request.query,
        top_k=request.top_k,
    )