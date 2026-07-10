from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class VideoBase(BaseModel):
    """Base schema for Video."""
    title: str
    filename: str
    language: str
    duration: int

class VideoCreate(VideoBase):
    """Schema for creating a video."""
    pass

class VideoUpdate(BaseModel):
    """Schema for updating a video."""
    title: str | None = None
    language: str | None = None
    status: str | None = None

class VideoRead(VideoBase):
    """Schema for reading video data."""
    id: int
    owner_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
    )