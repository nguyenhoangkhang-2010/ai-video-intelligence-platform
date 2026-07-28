import logging

from fastapi import APIRouter

from app.schemas.search import SearchRequest
from app.schemas.search import SemanticSearchResponse
from app.services.semantic_search import SemanticSearchService


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


service = SemanticSearchService()


@router.post(
    "/videos/{video_id}",
    response_model=SemanticSearchResponse,
)
def search_video(
    video_id: int,
    request: SearchRequest,
):
    """
    Semantic search inside video content.
    """

    logger.info(
        "Searching video %s with query: %s",
        video_id,
        request.query,
    )

    results = service.search(
        query=request.query,
        top_k=request.top_k,
    )

    return {
        "video_id": video_id,
        "query": request.query,
        "results": results,
    }