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