from sqlalchemy.orm import Session

from app.models.visual_segment import VisualSegment
from app.repositories.base import BaseRepository


class VisualSegmentRepository(BaseRepository[VisualSegment]):
    """Repository for VisualSegment model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=VisualSegment,
        )

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[VisualSegment]:

        return (
            self.db.query(VisualSegment)
            .filter(VisualSegment.video_id == video_id)
            .order_by(VisualSegment.start_time)
            .all()
        )

    def replace_for_video(
        self,
        video_id: int,
        new_segments: list[VisualSegment],
    ) -> list[VisualSegment]:
        """
        Delete-old + insert-new in one transaction - same all-or-
        nothing guarantee as ChapterRepository.replace_for_video.
        """

        try:
            (
                self.db.query(VisualSegment)
                .filter(VisualSegment.video_id == video_id)
                .delete(synchronize_session=False)
            )

            self.db.add_all(new_segments)
            self.db.commit()

            for segment in new_segments:
                self.db.refresh(segment)

            return new_segments
        except Exception:
            self.db.rollback()
            raise

    def set_speech_similarity(
        self,
        similarities: dict[int, float | None],
    ) -> None:
        """Store each segment id's speech similarity, in one commit."""

        for segment_id, similarity in similarities.items():
            (
                self.db.query(VisualSegment)
                .filter(VisualSegment.id == segment_id)
                .update({"speech_similarity": similarity}, synchronize_session=False)
            )

        self.db.commit()
