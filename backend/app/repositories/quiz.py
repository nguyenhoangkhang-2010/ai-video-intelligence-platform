from sqlalchemy.orm import Session

from app.models.quiz import Quiz
from app.repositories.base import BaseRepository


class QuizRepository(BaseRepository[Quiz]):
    """Repository for Quiz model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Quiz,
        )

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Quiz]:

        return (
            self.db.query(Quiz)
            .filter(Quiz.video_id == video_id)
            .all()
        )

    def get_by_type(
        self,
        video_id: int,
        quiz_type: str,
    ) -> list[Quiz]:

        return (
            self.db.query(Quiz)
            .filter(
                Quiz.video_id == video_id,
                Quiz.type == quiz_type,
            )
            .all()
        )