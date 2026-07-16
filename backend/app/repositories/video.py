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
        
    def get_by_id_and_owner(
        self,
        video_id: int,
        owner_id: int,
    ) -> Video | None:
        """
        Get a video by its ID that belongs to the specified owner.
        """
        return (
            self.db.query(Video)
            .filter(
                Video.id == video_id,
                Video.owner_id == owner_id,
            )
            .first()
        )
        
    def delete_by_owner(
        self,
        video_id: int,
        owner_id: int,
    ) -> bool:
        video = (
            self.db.query(Video)
            .filter(
                Video.id == video_id,
                Video.owner_id == owner_id,
            )
            .first()
        )

        if video is None:
            return False

        self.db.delete(video)
        self.db.commit()

        return True
    
    def update(
        self,
        video: Video,
    ):
        self.db.commit()
        self.db.refresh(video)

        return video