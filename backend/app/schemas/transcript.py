from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


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

class TranscriptUpdate(BaseModel):
    language: str | None = None
    text: str | None = None

class TranscriptRead(TranscriptBase):
    id: int
    video_id: int
    word_count: int
    created_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
    )