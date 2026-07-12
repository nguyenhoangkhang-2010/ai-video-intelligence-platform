from app.repositories.video import VideoRepository


class VideoService:
    """Service for video business logic."""

    def __init__(
        self,
        repository: VideoRepository,
    ):
        self.repository = repository

    def get_user_videos(
        self,
        user_id: int,
    ):
        return self.repository.get_by_owner(
            owner_id=user_id,
        )