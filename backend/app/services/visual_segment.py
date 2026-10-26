from app.models.visual_segment import VisualSegment
from app.repositories.visual_segment import VisualSegmentRepository
from app.schemas.visual_segment import VisualSegmentCreate


class VisualSegmentService:
    """Service for VisualSegment operations."""

    def __init__(
        self,
        repository: VisualSegmentRepository,
    ):
        self.repository = repository

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[VisualSegment]:
        return self.repository.get_by_video_id(
            video_id,
        )

    def get_by_id(
        self,
        segment_id: int,
    ) -> VisualSegment | None:
        return self.repository.get_by_id(
            segment_id,
        )

    def replace_for_video(
        self,
        video_id: int,
        segments_data: list[VisualSegmentCreate],
    ) -> list[VisualSegment]:
        return self.repository.replace_for_video(
            video_id,
            [VisualSegment(**data.model_dump()) for data in segments_data],
        )

    def set_speech_similarity(
        self,
        similarities: dict[int, float | None],
    ) -> None:
        self.repository.set_speech_similarity(
            similarities,
        )
