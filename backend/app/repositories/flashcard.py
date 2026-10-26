from sqlalchemy.orm import Session

from app.models.flashcard import Flashcard
from app.repositories.base import BaseRepository


class FlashcardRepository(BaseRepository[Flashcard]):
    """Repository for Flashcard model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Flashcard,
        )

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Flashcard]:

        return (
            self.db.query(Flashcard)
            .filter(Flashcard.video_id == video_id)
            .order_by(Flashcard.id)
            .all()
        )

    def get_by_difficulty(
        self,
        video_id: int,
        difficulty: str,
    ) -> list[Flashcard]:

        return (
            self.db.query(Flashcard)
            .filter(
                Flashcard.video_id == video_id,
                Flashcard.difficulty == difficulty,
            )
            .all()
        )

    def delete_by_video_id(
        self,
        video_id: int,
    ) -> None:
        """
        Bulk-delete all flashcards belonging to a video in a single
        statement/commit (used when replacing a video's flashcards on
        reprocess) - mirrors ChapterRepository.delete_by_video_id.
        """

        (
            self.db.query(Flashcard)
            .filter(Flashcard.video_id == video_id)
            .delete(synchronize_session=False)
        )

        self.db.commit()

    def replace_for_video(
        self,
        video_id: int,
        new_flashcards: list[Flashcard],
    ) -> list[Flashcard]:
        """
        Atomically replace every flashcard row for `video_id`: delete
        the old rows and insert `new_flashcards` in one transaction -
        mirrors EmbeddingRepository.replace_for_video. A single
        commit means this can only ever land in one of two states -
        every old row gone and every new row present, or (on any
        failure, via the rollback below) every old row still exactly
        as it was - never the previous delete-then-per-row-insert
        loop's partial-mix failure mode.
        """

        try:
            (
                self.db.query(Flashcard)
                .filter(Flashcard.video_id == video_id)
                .delete(synchronize_session=False)
            )

            self.db.add_all(new_flashcards)
            self.db.commit()

            for flashcard in new_flashcards:
                self.db.refresh(flashcard)

            return new_flashcards
        except Exception:
            self.db.rollback()
            raise