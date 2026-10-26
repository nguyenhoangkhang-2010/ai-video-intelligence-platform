from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator


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
    # "speech" (Whisper), or "visual" for a video with no speech whose
    # transcript was built from its on-screen content.
    source: Literal["speech", "visual"] = "speech"

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
    source: Literal["speech", "visual"] = "speech"

    @field_validator("source", mode="before")
    @classmethod
    def _unset_source_is_speech(cls, value):
        # Only an explicit "visual" is visual; unset (an ORM object not
        # yet flushed has no column default applied) means speech.
        return "visual" if value == "visual" else "speech"

    model_config = ConfigDict(
        from_attributes=True,
    )
