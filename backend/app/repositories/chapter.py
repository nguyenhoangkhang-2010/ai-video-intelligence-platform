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

    def delete_by_video_id(
        self,
        video_id: int,
    ) -> None:
        """
        Bulk-delete all chapters belonging to a video in a single
        statement/commit (used when replacing a video's chapters on
        reprocess) - mirrors EmbeddingRepository.delete_by_video_id.
        """

        (
            self.db.query(Chapter)
            .filter(Chapter.video_id == video_id)
            .delete(synchronize_session=False)
        )

        self.db.commit()