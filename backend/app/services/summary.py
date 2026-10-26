from app.models.summary import Summary
from app.repositories.summary import SummaryRepository
from app.schemas.summary import SummaryCreate


class SummaryService:
    """Service for Summary operations."""

    def __init__(
        self,
        repository: SummaryRepository,
    ):
        self.repository = repository

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Summary]:
        """
        Get all summaries of a video.
        """
        return self.repository.get_by_video_id(
            video_id,
        )

    def get_by_video_and_type(
        self,
        video_id: int,
        summary_type: str,
    ) -> Summary | None:
        """
        Get summary by video and summary type.
        """
        return self.repository.get_by_video_and_type(
            video_id,
            summary_type,
        )

    def create_summary(
        self,
        summary_data: SummaryCreate,
    ) -> Summary:
        """
        Create summary if it does not already exist.
        """
        existing = self.repository.get_by_video_and_type(
            video_id=summary_data.video_id,
            summary_type=summary_data.type,
        )

        if existing is not None:
            return existing

        summary = Summary(
            **summary_data.model_dump(),
        )

        return self.repository.create(summary)

    def save_summary(
        self,
        summary_data: SummaryCreate,
    ) -> Summary:
        """
        Create or update summary.
        """
        summary = self.repository.get_by_video_and_type(
            video_id=summary_data.video_id,
            summary_type=summary_data.type,
        )

        if summary is None:
            summary = Summary(
                **summary_data.model_dump(),
            )
            return self.repository.create(summary)

        summary.content = summary_data.content
        summary.model_name = summary_data.model_name

        return self.repository.update(summary)