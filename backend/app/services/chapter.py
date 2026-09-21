from app.models.chapter import Chapter
from app.repositories.chapter import ChapterRepository
from app.schemas.chapter import ChapterCreate


class ChapterService:
    """Service for Chapter operations."""

    def __init__(
        self,
        repository: ChapterRepository,
    ):
        self.repository = repository

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Chapter]:
        """
        Get all chapters of a video, ordered by start time.
        """
        return self.repository.get_by_video_id(
            video_id,
        )

    def delete_by_video_id(
        self,
        video_id: int,
    ) -> None:
        """
        Delete all chapters belonging to a video.
        """
        self.repository.delete_by_video_id(
            video_id,
        )

    def create_chapter(
        self,
        chapter_data: ChapterCreate,
    ) -> Chapter:
        """
        Create a chapter.
        """
        chapter = Chapter(
            **chapter_data.model_dump(),
        )

        return self.repository.create(
            chapter,
        )
