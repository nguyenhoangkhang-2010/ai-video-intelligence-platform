from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.schemas.transcript import TranscriptRead
from app.services.transcript import TranscriptService
from app.services.video import VideoService
from app.api.deps import get_transcript_service
from app.api.deps import get_video_service


router = APIRouter(
    prefix="/transcripts",
    tags=["Transcripts"],
)


@router.get(
    "/{video_id}",
    response_model=TranscriptRead,
)
def get_transcript_by_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    service: TranscriptService = Depends(
        get_transcript_service
    ),
):
    """
    Get the transcript for a video.

    Ownership-checked exactly like every other video-scoped resource
    endpoint (summaries, translations, quizzes, chapters, flashcards)
    - this previously had no authentication/ownership check at all,
    letting any caller read any video's transcript by guessing an id.
    """

    # check ownership
    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    transcript = service.get_by_video_id(
        video_id
    )

    if transcript is None:
        raise HTTPException(
            status_code=404,
            detail="Transcript not found",
        )

    return transcript