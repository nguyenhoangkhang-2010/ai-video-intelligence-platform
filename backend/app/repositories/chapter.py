from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.repositories.base import BaseRepository


class ChapterRepository(BaseRepository[Chapter]):
    """Repository for Chapter model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Chapter,
        )

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Chapter]:

        return (
            self.db.query(Chapter)
            .filter(Chapter.video_id == video_id)
            .order_by(Chapter.start_time)
            .all()
        )