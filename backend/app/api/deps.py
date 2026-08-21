from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.session import get_db

from app.repositories.video import VideoRepository
from app.services.video import VideoService

from app.repositories.processing_job import ProcessingJobRepository
from app.services.processing_job import ProcessingJobService

from app.repositories.transcript import TranscriptRepository
from app.services.transcript import TranscriptService

from app.repositories.quiz import QuizRepository
from app.services.quiz import QuizService

from app.repositories.summary import SummaryRepository
from app.services.summary import SummaryService

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

def get_transcript_service(
    db: Session = Depends(get_db),
) -> TranscriptService:
    repository = TranscriptRepository(db)
    return TranscriptService(repository)

def get_quiz_service(
    db: Session = Depends(get_db),
) -> QuizService:
    repository = QuizRepository(db)
    return QuizService(repository)

def get_summary_service(
    db: Session = Depends(get_db),
) -> SummaryService:
    repository = SummaryRepository(db)
    return SummaryService(repository)