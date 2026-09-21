import logging

from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.api.deps import get_processing_job_service
from app.api.deps import get_quiz_service
from app.api.deps import get_summary_service
from app.api.deps import get_transcript_service
from app.api.deps import get_translation_service
from app.api.deps import get_video_service

from app.services.processing_job import ProcessingJobService
from app.services.quiz import QuizService
from app.services.summary import SummaryService
from app.services.transcript import TranscriptService
from app.services.translation import TranslationService
from app.services.video import VideoService

from app.schemas.meeting import MeetingResponse
from app.schemas.processing_job import ProcessingJobRead
from app.schemas.quiz import QuizRead
from app.schemas.summary import SummaryRead
from app.schemas.transcript import TranscriptRead
from app.schemas.translation import TranslationRead
from app.schemas.video import VideoRead


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/meetings",
    tags=["Meetings"],
)


@router.get(
    "/{video_id}",
    response_model=MeetingResponse,
)
def get_meeting(
    video_id: int,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    transcript_service: TranscriptService = Depends(
        get_transcript_service,
    ),
    summary_service: SummaryService = Depends(get_summary_service),
    translation_service: TranslationService = Depends(
        get_translation_service,
    ),
    quiz_service: QuizService = Depends(get_quiz_service),
    processing_job_service: ProcessingJobService = Depends(
        get_processing_job_service,
    ),
):
    """
    Aggregated meeting view.

    A meeting recording is a Video - there is no separate Meeting
    domain. This composes the existing video/transcript/summary/
    translation/quiz/processing-job services, each already exposed by
    its own dedicated endpoint, into a single response for a meeting
    workspace UI.
    """

    video = video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    logger.info(
        "Building meeting view for video %s.",
        video_id,
    )

    transcript = transcript_service.get_by_video_id(
        video_id,
    )

    return MeetingResponse(
        video=VideoRead.model_validate(video),
        processing_jobs=[
            ProcessingJobRead.model_validate(job)
            for job in processing_job_service.get_jobs_by_video(
                video_id=video_id,
            )
        ],
        transcript=(
            TranscriptRead.model_validate(transcript)
            if transcript is not None
            else None
        ),
        summaries=[
            SummaryRead.model_validate(summary)
            for summary in summary_service.get_by_video_id(
                video_id=video_id,
            )
        ],
        translations=[
            TranslationRead.model_validate(translation)
            for translation in translation_service.get_by_video_id(
                video_id=video_id,
            )
        ],
        quizzes=[
            QuizRead.model_validate(quiz)
            for quiz in quiz_service.get_by_video_id(
                video_id=video_id,
            )
        ],
    )
