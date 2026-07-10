from sqlalchemy.orm import Session

from app.models.summary import Summary
from app.repositories.base import BaseRepository

class SummaryRepository(BaseRepository[Summary]):
    """Repository for Summary model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Summary,
        )

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Summary]:

        return (
            self.db.query(Summary)
            .filter(Summary.video_id == video_id)
            .all()
        )

    def get_by_video_and_type(
        self,
        video_id: int,
        summary_type: str,
    ) -> Summary | None:

        return (
            self.db.query(Summary)
            .filter(
                Summary.video_id == video_id,
                Summary.type == summary_type,
            )
            .first()
        )