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