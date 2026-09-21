import mimetypes

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import File
from fastapi import status
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse

from app.auth.dependencies import get_current_user
from app.auth.dependencies import get_current_user_for_media
from app.models.user import User

from app.utils.ffprobe import extract_metadata

from app.api.deps import get_video_service
from app.api.deps import get_processing_job_service
from app.api.deps import get_upload_pipeline
from app.api.deps import get_storage_backend

from app.pipelines.upload_pipeline import UploadPipeline
from app.services.processing_job import ProcessingJobService
from app.services.video import VideoService
from app.schemas.video import VideoRead
from app.schemas.video import VideoUpdate
from app.schemas.video import VideoStatusResponse

from app.schemas.processing_job import ProcessingJobRead

from app.storage.base import StorageBackend

import uuid
import shutil

from app.config.settings import VIDEO_UPLOAD_DIR

router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
)

# Videos are saved to VIDEO_UPLOAD_DIR/{filename} today (see
# upload_video below) - VIDEO_UPLOAD_DIR is STORAGE_DIR / "videos",
# so this key is exactly what a StorageBackend rooted at STORAGE_DIR
# (the default for every backend - see app/storage/) resolves to the
# same physical location, with no change to how upload_video writes
# the file.
def _video_storage_key(filename: str) -> str:
    return f"videos/{filename}"

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
    "/{video_id}/stream",
)
def stream_video(
    video_id: int,
    current_user: User = Depends(get_current_user_for_media),
    service: VideoService = Depends(get_video_service),
    storage: StorageBackend = Depends(get_storage_backend),
):
    """
    Deliver the uploaded video file for playback.

    Authenticated (accepts a `token` query parameter as a fallback to
    the Authorization header, since a browser <video> element cannot
    attach custom headers - see get_current_user_for_media) and
    ownership-checked exactly like every other /videos/{video_id}/...
    endpoint.

    Goes entirely through the StorageBackend abstraction (see
    app/storage/) rather than hardcoding a filesystem path here: if
    the configured backend can hand back a direct URL (e.g. an S3/
    MinIO presigned URL), the client is redirected there so the bytes
    never pass through this process; otherwise the local file is
    served directly via FileResponse, which natively supports HTTP
    Range requests (seeking) without loading the file into memory.
    """
    video = service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    key = _video_storage_key(video.filename)

    url = storage.get_url(key)
    if url is not None:
        return RedirectResponse(
            url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    path = storage.get_local_path(key)
    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found",
        )

    media_type, _ = mimetypes.guess_type(path.name)

    return FileResponse(
        path,
        media_type=media_type or "application/octet-stream",
    )

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
    video = service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    return processing_service.get_jobs_by_video(
        video_id=video.id,
    )
    
@router.post(
    "/upload",
    response_model=VideoRead,
)
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(get_video_service),
    upload_pipeline: UploadPipeline = Depends(
        get_upload_pipeline,
    ),
):
    """
    Upload a video file.
    """
    VIDEO_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    unique_filename = (
        f"{uuid.uuid4()}_{file.filename}"
    )

    file_path = VIDEO_UPLOAD_DIR / unique_filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer,
        )
        
    metadata = extract_metadata(
        str(file_path)
    )
    video = service.upload_video(
        owner_id=current_user.id,
        title=file.filename,
        filename=unique_filename,
        language="unknown",  # TODO: Detect language using Whisper
        duration=metadata.duration,          # TODO: Extract duration using FFmpeg
    )

    upload_pipeline.process(
        video_id=video.id,
        video_path=str(file_path),
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
        status=video_update.status,
    )
    