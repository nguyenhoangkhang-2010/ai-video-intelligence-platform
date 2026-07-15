from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.session import get_db

from app.repositories.video import VideoRepository
from app.services.video import VideoService

from app.repositories.processing_job import ProcessingJobRepository
from app.services.processing_job import ProcessingJobService

def get_video_service(
    db: Session = Depends(get_db),
) -> VideoService:
    """
    Dependency that provides a VideoService instance.
    """
    repository = VideoRepository(db)

    return VideoService(repository)

def get_processing_job_service(
    db: Session = Depends(get_db),
) -> ProcessingJobService:
    repository = ProcessingJobRepository(db)
    return ProcessingJobService(repository)