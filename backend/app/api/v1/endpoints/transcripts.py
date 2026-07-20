from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.schemas.transcript import TranscriptRead
from app.services.transcript import TranscriptService
from app.api.deps import get_transcript_service


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
    service: TranscriptService = Depends(
        get_transcript_service
    ),
):

    transcript = service.get_by_video_id(
        video_id
    )

    if transcript is None:
        raise HTTPException(
            status_code=404,
            detail="Transcript not found",
        )

    return transcript