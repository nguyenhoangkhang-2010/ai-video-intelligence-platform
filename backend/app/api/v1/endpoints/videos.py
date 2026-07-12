from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.api.deps import get_video_service

from app.services.video import VideoService
from app.schemas.video import VideoRead

router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
)

@router.get(
    "",
    response_model=list[VideoRead],
)
def get_my_videos(
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(get_video_service),
): 
    """
    Get all videos of current user.
    """
    return service.get_user_videos(
        user_id=current_user.id,
    )
    
@router.get(
    "/{video_id}",
    response_model=VideoRead,
)
def get_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(get_video_service),
):
    """
    Get a single video by ID.
    """
    return service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )