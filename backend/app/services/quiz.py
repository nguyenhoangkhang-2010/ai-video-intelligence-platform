from app.models.quiz import Quiz
from app.repositories.quiz import QuizRepository
from app.schemas.quiz import QuizCreate


class QuizService:
    """Service for Quiz operations."""

    def __init__(
        self,
        repository: QuizRepository,
    ):
        self.repository = repository


    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Quiz]:

        return self.repository.get_by_video_id(
            video_id,
        )

    def delete_by_video_id(
        self,
        video_id: int,
    ) -> None:
        """
        Delete all quizzes belonging to a video.
        """
        self.repository.delete_by_video_id(
            video_id,
        )

    def create_quiz(
        self,
        quiz_data: QuizCreate,
    ) -> Quiz:

        quiz = Quiz(
            **quiz_data.model_dump(),
        )

        return self.repository.create(
            quiz,
        )

    def replace_for_video(
        self,
        video_id: int,
        quizzes_data: list[QuizCreate],
    ) -> list[Quiz]:
        """
        Atomically replace every quiz row for `video_id` with
        `quizzes_data` - see QuizRepository.replace_for_video for the
        consistency guarantee this provides.
        """
        new_rows = [
            Quiz(**data.model_dump())
            for data in quizzes_data
        ]

        return self.repository.replace_for_video(
            video_id,
            new_rows,
        )