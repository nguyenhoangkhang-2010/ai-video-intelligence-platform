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

    def delete_by_video_id(
        self,
        video_id: int,
    ) -> None:
        """
        Bulk-delete all quizzes belonging to a video in a single
        statement/commit (used when replacing a video's quizzes on
        reprocess) - mirrors ChapterRepository.delete_by_video_id.
        """

        (
            self.db.query(Quiz)
            .filter(Quiz.video_id == video_id)
            .delete(synchronize_session=False)
        )

        self.db.commit()