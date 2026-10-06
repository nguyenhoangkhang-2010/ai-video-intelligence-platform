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

    def replace_for_video(
        self,
        video_id: int,
        new_chapters: list[Chapter],
    ) -> list[Chapter]:
        """
        Atomically replace every chapter row for `video_id`: delete
        the old rows and insert `new_chapters` in one transaction -
        mirrors EmbeddingRepository.replace_for_video. A single
        commit means this can only ever land in one of two states -
        every old row gone and every new row present, or (on any
        failure, via the rollback below) every old row still exactly
        as it was - never the previous delete-then-per-row-insert
        loop's partial-mix failure mode.
        """

        try:
            (
                self.db.query(Chapter)
                .filter(Chapter.video_id == video_id)
                .delete(synchronize_session=False)
            )

            self.db.add_all(new_chapters)
            self.db.commit()

            for chapter in new_chapters:
                self.db.refresh(chapter)

            return new_chapters
        except Exception:
            self.db.rollback()
            raise