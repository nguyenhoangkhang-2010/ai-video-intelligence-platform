from sqlalchemy.orm import Session

from app.models.translation import Translation
from app.repositories.base import BaseRepository


class TranslationRepository(BaseRepository[Translation]):
    """Repository for Translation model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Translation,
        )

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Translation]:

        return (
            self.db.query(Translation)
            .filter(Translation.video_id == video_id)
            .all()
        )

    def get_by_video_and_language(
        self,
        video_id: int,
        language: str,
    ) -> Translation | None:

        return (
            self.db.query(Translation)
            .filter(
                Translation.video_id == video_id,
                Translation.language == language,
            )
            .first()
        )