from app.models.transcript import Transcript
from app.repositories.transcript import TranscriptRepository


class TranscriptService:
    """Service for Transcript operations."""

    def __init__(
        self,
        repository: TranscriptRepository,
    ):
        self.repository = repository


    def get_by_video_id(
        self,
        video_id: int,
    ) -> Transcript | None:
        """
        Get transcript by video id.
        """

        return self.repository.get_by_video_id(
            video_id
        )