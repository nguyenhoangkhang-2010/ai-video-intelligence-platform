from sqlalchemy.orm import Session

from app.models.video import Video
from app.repositories.base import BaseRepository

class VideoRepository(BaseRepository[Video]):
    """Repository for Video model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Video,
        )

    def get_by_filename(
        self,
        filename: str,
    ) -> Video | None:

        return (
            self.db.query(Video)
            .filter(Video.filename == filename)
            .first()
        )

    def get_by_owner(
        self,
        owner_id: int,
    ) -> list[Video]:

        return (
            self.db.query(Video)
            .filter(Video.owner_id == owner_id)
            .all()
        )

    def get_by_status(
        self,
        status: str,
    ) -> list[Video]:

        return (
            self.db.query(Video)
            .filter(Video.status == status)
            .all()
        )