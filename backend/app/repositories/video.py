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
        limit: int = 200,
        offset: int = 0,
    ) -> list[Video]:
        """
        A user's own videos, newest first.

        Two real gaps closed here (found during a pagination/N+1
        audit, not a hypothetical): this query previously had no
        ORDER BY at all, so Postgres was free to return rows in any
        order it liked, and could silently reorder them between two
        otherwise-identical requests - the Library page's video order
        was technically undefined. It also had no LIMIT, so a single
        `GET /videos` call scaled linearly, unbounded, with however
        many videos a user has ever uploaded.

        `limit`/`offset` default to values that reproduce the old
        unbounded-in-practice behavior for every account that exists
        today (nowhere near 200 videos) while giving both real ones a
        ceiling - not a public, paginated API contract change: the
        endpoint's response shape is untouched (still a plain list),
        so nothing calling it today needs to change.
        """
        return (
            self.db.query(Video)
            .filter(Video.owner_id == owner_id)
            .order_by(Video.created_at.desc())
            .offset(offset)
            .limit(limit)
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
    ) -> Video:
        self.db.commit()
        self.db.refresh(video)

        return video