from sqlalchemy.orm import Session

from app.models.transcript import Transcript
from app.repositories.base import BaseRepository


class TranscriptRepository(BaseRepository[Transcript]):
    """Repository for Transcript model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Transcript,
        )

    def get_by_video_id(
        self,
        video_id: int,
    ) -> Transcript | None:

        return (
            self.db.query(Transcript)
            .filter(Transcript.video_id == video_id)
            .first()
        )
        
    def update(
        self,
        transcript: Transcript,
    ) -> Transcript:
        self.db.commit()
        self.db.refresh(transcript)
        return transcript
    
    def exists(
        self,
        video_id: int,
    ) -> bool:
        return (
            self.db.query(Transcript)
            .filter(
                Transcript.video_id == video_id,
            )
            .first()
            is not None
        )