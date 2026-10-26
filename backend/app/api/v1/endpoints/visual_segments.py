from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse

from ai.vision.segments import relation
from app.api.deps import get_storage_backend
from app.api.deps import get_video_service
from app.api.deps import get_visual_segment_service
from app.auth.dependencies import get_current_user
from app.auth.dependencies import get_current_user_for_media
from app.config.settings import settings
from app.models.user import User
from app.schemas.visual_segment import VisualSegmentRead
from app.services.video import VideoService
from app.services.visual_segment import VisualSegmentService
from app.storage.base import StorageBackend


router = APIRouter(
    prefix="/videos",
    tags=["Visual segments"],
)


@router.get(
    "/{video_id}/visual-segments",
    response_model=list[VisualSegmentRead],
)
def get_video_visual_segments(
    video_id: int,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    visual_service: VisualSegmentService = Depends(get_visual_segment_service),
):
    """
    What is on screen over the video, in order: on-screen text, a
    description of the picture, and how it relates to what was said
    ("illustrates", "unrelated" b-roll, or "no-speech").

    404 if the video is not the caller's. An empty list is a valid
    answer: visual analysis is best-effort (and can be disabled).
    """
    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    threshold = settings.vision.related_threshold
    return [
        VisualSegmentRead.model_validate(row).model_copy(
            update={
                "relation": relation(row.speech_similarity, threshold),
                "has_frame": bool(row.frame_key),
            }
        )
        for row in visual_service.get_by_video_id(video_id)
    ]


@router.get(
    "/{video_id}/visual-segments/{segment_id}/frame",
)
def get_visual_segment_frame(
    video_id: int,
    segment_id: int,
    current_user: User = Depends(get_current_user_for_media),
    video_service: VideoService = Depends(get_video_service),
    visual_service: VisualSegmentService = Depends(get_visual_segment_service),
    storage: StorageBackend = Depends(get_storage_backend),
):
    """
    The keyframe image of one visual segment. Same media auth (token
    query parameter, for <img>) and ownership rules as the thumbnail.
    """
    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    segment = visual_service.get_by_id(segment_id)
    if segment is None or segment.video_id != video_id or not segment.frame_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frame not available",
        )

    url = storage.get_url(segment.frame_key)
    if url is not None:
        return RedirectResponse(
            url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    path = storage.get_local_path(segment.frame_key)
    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frame not available",
        )

    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=3600"},
    )
