from fastapi import APIRouter
from fastapi import Depends
from fastapi import UploadFile
from fastapi import File
from fastapi import BackgroundTasks

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.api.deps import get_video_service
from app.api.deps import get_processing_job_service

from app.workers.video_processor import process_video
from app.services.processing_job import ProcessingJobService
from app.services.video import VideoService
from app.schemas.video import VideoRead
from app.schemas.video import VideoUpdate
from app.schemas.video import VideoStatusResponse

from app.schemas.processing_job import ProcessingJobRead

from pathlib import Path
import shutil

router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
)

@router.get(
    "",
    response_model=list[VideoRead],
)
def get_my_videos(
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(get_video_service),
): 
    """
    Get all videos of current user.
    """
    return service.get_user_videos(
        user_id=current_user.id,
    )
    
@router.get(
    "/{video_id}",
    response_model=VideoRead,
)
def get_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(get_video_service),
):
    """
    Get a single video by ID.
    """
    return service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )
    
@router.get(
    "/{video_id}/status",
    response_model=VideoStatusResponse,
)
def get_video_status(
    video_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(get_video_service),
):
    """
    Get processing status of a video.
    """
    video = service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    return video
    
@router.get(
    "/{video_id}/processing-jobs",
    response_model=list[ProcessingJobRead],
)
def get_processing_jobs(
    video_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(get_video_service),
    processing_service: ProcessingJobService = Depends(
        get_processing_job_service,
    ),
):
    """
    Get all processing jobs of a video.
    """
    service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    return processing_service.get_jobs_by_video(
        video_id=video_id,
    )
    
@router.post(
    "/upload",
    response_model=VideoRead,
)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(get_video_service),
    processing_service: ProcessingJobService = Depends(
        get_processing_job_service,
    ),
):
    """
    Upload a video file.
    """
    upload_dir = Path("uploads/videos")
    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = upload_dir / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer,
        )
    video = service.upload_video(
        owner_id=current_user.id,
        title=file.filename,
        filename=file.filename,
        language="unknown",  # TODO: Detect language using Whisper
        duration=0,          # TODO: Extract duration using FFmpeg
    )

    processing_service.create_processing_job(
        video_id=video.id,
    )
    
    background_tasks.add_task(
        process_video,
        video.id,
    )

    return video
    
@router.delete(
    "/{video_id}",
)
def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(get_video_service),
):
    """
    Delete a video.
    """
    return service.delete_video(
        video_id=video_id,
        user_id=current_user.id,
    )
    
@router.put(
    "/{video_id}",
    response_model=VideoRead,
)
def update_video(
    video_id: int,
    video_update: VideoUpdate,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(get_video_service),
):
    """
    Update video metadata.
    """
    return service.update_video(
        video_id=video_id,
        user_id=current_user.id,
        title=video_update.title,
        language=video_update.language,
    )