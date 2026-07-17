from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class ProcessingJobBase(BaseModel):
    """Base schema for ProcessingJob."""
    job_type: str
    status: str

class ProcessingJobCreate(ProcessingJobBase):
    """Schema for creating a processing job."""
    video_id: int

class ProcessingJobUpdate(BaseModel):
    """Schema for updating a processing job."""
    status: str | None = None
    error_message: str | None = None
    finished_at: datetime | None = None

class ProcessingJobStatusUpdate(BaseModel):
    """Schema for updating processing job status."""
    status: str
    error_message: str | None = None

class ProcessingJobRead(ProcessingJobBase):
    """Schema for reading processing job data."""
    id: int
    video_id: int
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    model_config = ConfigDict(
        from_attributes=True,
    )