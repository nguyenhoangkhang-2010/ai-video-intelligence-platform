from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.api.deps import get_summary_service
from app.api.deps import get_video_service

from app.services.summary import SummaryService
from app.services.video import VideoService

from app.schemas.summary import SummaryRead


router = APIRouter(
    prefix="/summaries",
    tags=["Summaries"],
)


@router.get(
    "/video/{video_id}",
    response_model=list[SummaryRead],
)
def get_video_summaries(
    video_id: int,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    summary_service: SummaryService = Depends(get_summary_service),
):
    """
    Get summaries generated from a video.
    """

    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    return summary_service.get_by_video_id(
        video_id=video_id,
    )