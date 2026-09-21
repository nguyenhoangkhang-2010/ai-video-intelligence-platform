from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.api.deps import get_chapter_service
from app.api.deps import get_video_service

from app.services.chapter import ChapterService
from app.services.video import VideoService

from app.schemas.chapter import ChapterRead


router = APIRouter(
    prefix="/videos",
    tags=["Chapters"],
)


@router.get(
    "/{video_id}/chapters",
    response_model=list[ChapterRead],
)
def get_video_chapters(
    video_id: int,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    """
    Get chapters detected for a video, ordered by start time.

    Raises 404 (via video_service.get_video) if the video does not
    exist or does not belong to the current user. An empty list is a
    valid response - chapter detection is best-effort and a short/
    simple video may legitimately have none.
    """

    # check ownership
    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    return chapter_service.get_by_video_id(
        video_id=video_id,
    )
