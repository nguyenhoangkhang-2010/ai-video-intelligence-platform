import logging

from fastapi import APIRouter

from app.services.semantic_search import SemanticSearchService


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


service = SemanticSearchService()


@router.post(
    "/videos/{video_id}",
)
def search_video(
    video_id: int,
    query: str,
):
    """
    Semantic search inside video content.
    """

    logger.info(
        "Searching video %s with query: %s",
        video_id,
        query,
    )

    results = service.search(
        query=query,
    )

    return {
        "video_id": video_id,
        "query": query,
        "results": results,
    }