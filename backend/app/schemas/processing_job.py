from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict

# The only values app/services/processing_job.py ever assigns to
# ProcessingJob.status. Constraining the client-writable schemas to
# this set (rather than an unrestricted str) stops PATCH
# /processing-jobs/{id} from accepting an arbitrary string; illegal
# but same-set transitions (e.g. COMPLETED -> PENDING) are further
# rejected by ProcessingJobService.update_job_status's own
# transition table.
ProcessingJobStatus = Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]

class ProcessingJobBase(BaseModel):
    """Base schema for ProcessingJob."""
    job_type: str
    status: ProcessingJobStatus

class ProcessingJobCreate(ProcessingJobBase):
    """Schema for creating a processing job."""
    video_id: int

class ProcessingJobUpdate(BaseModel):
    """Schema for updating a processing job."""
    status: ProcessingJobStatus | None = None
    error_message: str | None = None
    finished_at: datetime | None = None

class ProcessingJobStatusUpdate(BaseModel):
    """Schema for updating processing job status."""
    status: ProcessingJobStatus
    error_message: str | None = None

class ProcessingJobRead(ProcessingJobBase):
    """Schema for reading processing job data."""
    id: int
    video_id: int
    progress: int
    current_step: str | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    model_config = ConfigDict(
        from_attributes=True,
    )