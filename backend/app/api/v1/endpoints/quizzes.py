from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.api.deps import get_quiz_service
from app.api.deps import get_video_service

from app.services.quiz import QuizService
from app.services.video import VideoService

from app.schemas.quiz import QuizRead


router = APIRouter(
    prefix="/videos",
    tags=["Quizzes"],
)


@router.get(
    "/{video_id}/quizzes",
    response_model=list[QuizRead],
)
def get_video_quizzes(
    video_id: int,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    quiz_service: QuizService = Depends(get_quiz_service),
):
    """
    Get quizzes generated from a video.
    """

    # check ownership
    video_service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    return quiz_service.get_by_video_id(
        video_id=video_id,
    )