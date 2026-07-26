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
        Create transcript if it does not already exist.
        """
        existing = self.repository.get_by_video_id(
            transcript_data.video_id,
        )

        if existing is not None:
            return existing

        transcript = Transcript(
            **transcript_data.model_dump(),
            word_count=len(
                transcript_data.text.strip().split()
            ),
        )

        return self.repository.create(transcript)
    
    def save_transcript(
        self,
        transcript_data: TranscriptCreate,
    ) -> Transcript:

        transcript = self.repository.get_by_video_id(
            transcript_data.video_id
        )

        if transcript is None:
            transcript = Transcript(
                **transcript_data.model_dump(),
                word_count=len(
                    transcript_data.text.strip().split()
                ),
            )
            return self.repository.create(transcript)

        transcript.language = transcript_data.language
        transcript.text = transcript_data.text
        transcript.word_count = len(
            transcript_data.text.strip().split()
        )

        return self.repository.update(transcript)