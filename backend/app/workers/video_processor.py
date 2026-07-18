from app.database.session import SessionLocal

from app.repositories.video import VideoRepository
from app.services.video import VideoService
from app.pipelines.video_pipeline import VideoPipelineService

def process_video(
    video_id: int,
    file_path: str,
):
    """
    Background worker for processing uploaded videos.
    """
    db = SessionLocal()

    try:
        repository = VideoRepository(db)

        service = VideoService(repository)

        pipeline = VideoPipelineService(service)

        pipeline.process(
            video_id=video_id,
            file_path=file_path,
        )

    finally:
        db.close()