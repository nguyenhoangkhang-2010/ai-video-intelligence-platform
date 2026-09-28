from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.api.deps import get_chat_history_service
from app.api.deps import get_video_service

from app.services.chat_history import ChatHistoryService
from app.services.video import VideoService

from app.schemas.chat_history import ChatHistoryRead


router = APIRouter(
    prefix="/videos",
    tags=["Chat History"],
)


@router.get(
    "/{video_id}/chat-history",
    response_model=list[ChatHistoryRead],
)
def get_video_chat_history(
    video_id: int,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
):
    """
    This user's own past AI Chat turns for a video, oldest first.

    Scoped to `current_user.id` in addition to `video_id`, so the
    same video can never surface one user's questions to another
    (matters even though a video today only ever has one owner - this
    endpoint doesn't assume that stays true forever). Lets the AI Chat
    panel restore the conversation after a refresh or when reopening
    the video, instead of starting empty every time.
    """

    # check ownership
    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    return chat_history_service.get_by_user_and_video(
        user_id=current_user.id,
        video_id=video_id,
    )
