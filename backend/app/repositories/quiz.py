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
            .order_by(Quiz.id)
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

    def replace_for_video(
        self,
        video_id: int,
        new_quizzes: list[Quiz],
    ) -> list[Quiz]:
        """
        Atomically replace every quiz row for `video_id`: delete the
        old rows and insert `new_quizzes` in one transaction - mirrors
        EmbeddingRepository.replace_for_video. A single commit means
        this can only ever land in one of two states - every old row
        gone and every new row present, or (on any failure, via the
        rollback below) every old row still exactly as it was - never
        the previous delete-then-per-row-insert loop's partial-mix
        failure mode.
        """

        try:
            (
                self.db.query(Quiz)
                .filter(Quiz.video_id == video_id)
                .delete(synchronize_session=False)
            )

            self.db.add_all(new_quizzes)
            self.db.commit()

            for quiz in new_quizzes:
                self.db.refresh(quiz)

            return new_quizzes
        except Exception:
            self.db.rollback()
            raise