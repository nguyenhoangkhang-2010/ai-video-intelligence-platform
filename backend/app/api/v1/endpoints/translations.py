from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.api.deps import get_translation_service
from app.api.deps import get_video_service

from app.services.translation import TranslationService
from app.services.video import VideoService

from app.schemas.translation import TranslationRead


router = APIRouter(
    prefix="/translations",
    tags=["Translations"],
)


@router.get(
    "/video/{video_id}",
    response_model=list[TranslationRead],
)
def get_video_translations(
    video_id: int,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    translation_service: TranslationService = Depends(
        get_translation_service,
    ),
):
    """
    Get translations generated from a video.
    """

    # Check video ownership.
    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    return translation_service.get_by_video_id(
        video_id=video_id,
    )