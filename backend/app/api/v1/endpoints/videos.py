from fastapi import APIRouter
from fastapi import Depends
from fastapi import UploadFile
from fastapi import File

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.api.deps import get_video_service
from app.api.deps import get_processing_job_service

from app.services.processing_job import ProcessingJobService
from app.services.video import VideoService
from app.schemas.video import VideoRead

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
    
@router.post(
    "/upload",
    response_model=VideoRead,
)
async def upload_video(
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
    )

    processing_service.create_processing_job(
        video_id=video.id,
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