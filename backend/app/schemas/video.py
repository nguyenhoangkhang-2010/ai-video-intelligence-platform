from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict

# The only values app/services/video.py and app/pipelines/*.py ever
# assign to Video.status. Constraining VideoUpdate.status to this set
# (rather than an unrestricted str) stops a caller from writing an
# arbitrary string via PUT /videos/{id} and having the API silently
# accept it as if it were a real lifecycle state.
VideoStatus = Literal["uploaded", "processing", "processed", "failed"]

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
    status: VideoStatus | None = None

class VideoRead(VideoBase):
    """Schema for reading video data."""
    id: int
    owner_id: int
    status: VideoStatus
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
    )

class VideoStatusResponse(BaseModel):
    """Schema for video processing status."""

    id: int
    status: VideoStatus

    model_config = ConfigDict(
        from_attributes=True,
    )