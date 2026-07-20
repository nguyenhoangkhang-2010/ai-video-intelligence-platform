from app.models.transcript import Transcript
from app.repositories.transcript import TranscriptRepository
from app.schemas.transcript import TranscriptCreate


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
        
    def create_transcript(
        self,
        transcript_data: TranscriptCreate,
    ) -> Transcript:
        """
        Create a transcript.
        """
        transcript = Transcript(
            **transcript_data.model_dump(),
            word_count=len(
                transcript_data.text.split()
            ),
        )

        return self.repository.create(
            transcript
        )