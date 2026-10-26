from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class TranscriptSegment(BaseModel):
    """One timed piece of speech, in video seconds."""

    start: float = Field(ge=0)
    end: float = Field(ge=0)
    text: str
    speaker: str | None = None


class TranscriptBase(BaseModel):
    language: str = Field(
        min_length=2,
        max_length=20,
    )

    text: str = Field(
        min_length=1,
    )

class TranscriptCreate(TranscriptBase):
    video_id: int
    # Whisper's timed segments, in order. Optional so callers that only
    # have plain text (and older tests) keep working.
    segments: list[TranscriptSegment] | None = None

class TranscriptUpdate(BaseModel):
    language: str | None = None
    text: str | None = None

class TranscriptRead(TranscriptBase):
    id: int
    video_id: int
    word_count: int
    created_at: datetime
    # None for transcripts saved before timed segments were stored.
    segments: list[TranscriptSegment] | None = None
    model_config = ConfigDict(
        from_attributes=True,
    )
