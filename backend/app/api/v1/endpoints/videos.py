import logging
import mimetypes

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import File
from fastapi import status
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse
from starlette.concurrency import run_in_threadpool

from app.auth.dependencies import get_current_user
from app.auth.dependencies import get_current_user_for_media
from app.models.user import User

from app.utils.ffprobe import extract_metadata

from app.api.deps import get_video_service
from app.api.deps import get_processing_job_service
from app.api.deps import get_upload_pipeline
from app.api.deps import get_storage_backend
from app.api.deps import get_embedding_service

from app.pipelines.upload_pipeline import UploadPipeline
from app.services.processing_job import ProcessingJobService
from app.services.video import VideoService
from app.services.embedding import EmbeddingService
from app.schemas.video import VideoRead
from app.schemas.video import VideoUpdate
from app.schemas.video import VideoStatusResponse

from app.schemas.processing_job import ProcessingJobRead

from app.storage.base import StorageBackend

from app.config.settings import settings
from app.core.rate_limit import rate_limit

from ai.embedding.vector_store import VectorStore

from app.utils.uploads import (
    sanitize_filename,
    save_upload_within_limit,
    validate_upload_extension,
)

import uuid

from app.config.settings import VIDEO_UPLOAD_DIR

router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
)

logger = logging.getLogger(__name__)

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
    "/{video_id}/thumbnail",
)
def get_video_thumbnail(
    video_id: int,
    current_user: User = Depends(get_current_user_for_media),
    service: VideoService = Depends(get_video_service),
    storage: StorageBackend = Depends(get_storage_backend),
):
    """
    Deliver this video's real, ffmpeg-extracted representative frame.

    Same authentication (accepts a `token` query parameter, since a
    browser <img> element cannot attach custom headers either) and
    ownership pattern as stream_video above - one user's thumbnail is
    never reachable via another user's session. 404s both when the
    video isn't the caller's (ownership check, via get_video) and
    when it is but no thumbnail exists yet - extraction runs early in
    the processing pipeline (see VideoPipelineService.metadata_stage)
    and is best-effort, so a video that's still processing, or one
    whose extraction genuinely failed, correctly has none. The
    frontend distinguishes those two real states from `video.status`,
    not from this endpoint's response - see services/videos.ts.

    Response carries a real Cache-Control (the underlying frame for a
    given video never changes once extracted, so a long-lived
    immutable cache is honest, not merely convenient) rather than the
    framework's default of no caching at all.
    """
    video = service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    if not video.thumbnail_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not available",
        )

    url = storage.get_url(video.thumbnail_key)
    if url is not None:
        return RedirectResponse(
            url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    path = storage.get_local_path(video.thumbnail_key)
    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not available",
        )

    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
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
    dependencies=[Depends(rate_limit("upload", settings.rate_limit.upload_limit, 3600))],
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

    The chunked disk write and the ffprobe subprocess call are both
    genuinely blocking (synchronous file I/O and `subprocess.run`
    respectively) - run via `run_in_threadpool` rather than directly
    in this `async def` body, so a large upload can no longer stall
    the single event loop (and therefore every other concurrent
    request) for its full duration. The AI processing pipeline itself
    was already correctly backgrounded via Celery before this change;
    this closes the one remaining synchronous-blocking gap in the
    upload path itself.
    """
    VIDEO_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = sanitize_filename(file.filename or "")
    validate_upload_extension(safe_filename)

    unique_filename = (
        f"{uuid.uuid4()}_{safe_filename}"
    )

    file_path = VIDEO_UPLOAD_DIR / unique_filename

    await run_in_threadpool(
        save_upload_within_limit,
        file,
        file_path,
    )

    metadata = await run_in_threadpool(
        extract_metadata,
        str(file_path),
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
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    storage: StorageBackend = Depends(get_storage_backend),
):
    """
    Delete a video and every artifact derived from it.

    Database rows (transcript, summaries, translations, chapters,
    quizzes, flashcards, embeddings, processing jobs) are already
    covered by ON DELETE CASCADE. This additionally removes the two
    things that live outside the database and were previously left
    behind forever: the uploaded source file (via the same
    StorageBackend the stream endpoint reads through) and this
    video's vectors in the shared FAISS index (via VectorStore.replace,
    the same mechanism used to swap embeddings on reprocessing).

    Ownership is checked first (get_video 404s if this video isn't
    the caller's), exactly as every other video-scoped endpoint - the
    cleanup below never runs against a video the caller doesn't own.
    """
    video = service.get_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    filename = video.filename
    thumbnail_key = video.thumbnail_key
    vector_ids = {
        embedding.vector_id
        for embedding in embedding_service.get_by_video_id(video_id)
    }

    result = service.delete_video(
        video_id=video_id,
        user_id=current_user.id,
    )

    # Best-effort from here: the database row is already gone (the
    # deletion itself already succeeded), so a storage/FAISS cleanup
    # failure is logged rather than turned into an error response -
    # the same "cleanup is best-effort, not transactional with the
    # DB" posture this project already takes in video_pipeline.py's
    # embedding_stage.
    if thumbnail_key:
        try:
            storage.delete(thumbnail_key)
        except Exception:
            logger.exception(
                "Failed to delete stored thumbnail for video %s (key=%s).",
                video_id,
                thumbnail_key,
            )

    try:
        storage.delete(_video_storage_key(filename))
    except Exception:
        logger.exception(
            "Failed to delete stored file for video %s (filename=%s).",
            video_id,
            filename,
        )

    if vector_ids:
        try:
            VectorStore(dimension=1024).replace(
                remove_vector_ids=vector_ids,
                vectors=[],
                vector_ids=[],
            )
        except Exception:
            logger.exception(
                "Failed to remove FAISS vectors for video %s.",
                video_id,
            )

    return result
    
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
    