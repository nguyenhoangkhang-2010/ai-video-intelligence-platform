from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.api.deps import get_processing_job_service
from app.services.processing_job import ProcessingJobService
from app.schemas.processing_job import ProcessingJobRead
from app.schemas.processing_job import ProcessingJobStatusUpdate

router = APIRouter(
    prefix="/processing-jobs",
    tags=["Processing Jobs"],
)

@router.get(
    "",
    response_model=list[ProcessingJobRead],
)
def get_processing_jobs(
    current_user: User = Depends(get_current_user),
    service: ProcessingJobService = Depends(
        get_processing_job_service,
    ),
):
    """
    Get all processing jobs belonging to the current user's own
    videos.

    Previously unauthenticated and unscoped, returning every job for
    every user - fixed to require authentication and to filter by
    ownership, consistent with every other resource in this API.
    """
    return service.get_jobs_for_user(
        user_id=current_user.id,
    )

@router.get(
    "/{job_id}",
    response_model=ProcessingJobRead,
)
def get_processing_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    service: ProcessingJobService = Depends(
        get_processing_job_service,
    ),
):
    """
    Get processing job by ID, only if it belongs to the current
    user's own video.

    Previously unauthenticated and unscoped, letting any caller read
    any job by guessing an id - fixed to require authentication and
    ownership, matching every other resource in this API.
    """
    return service.get_job_for_user(
        job_id=job_id,
        user_id=current_user.id,
    )

@router.patch(
    "/{job_id}",
    response_model=ProcessingJobRead,
)
def update_processing_job(
    job_id: int,
    job_update: ProcessingJobStatusUpdate,
    current_user: User = Depends(get_current_user),
    service: ProcessingJobService = Depends(
        get_processing_job_service,
    ),
):
    """
    Update processing job status.

    Previously unauthenticated and unscoped, letting any caller
    overwrite any job's status by guessing an id - fixed to require
    authentication and ownership (get_job_for_user raises 404 if the
    job doesn't belong to the current user's own video, before any
    mutation happens).
    """
    service.get_job_for_user(
        job_id=job_id,
        user_id=current_user.id,
    )

    return service.update_job_status(
        job_id=job_id,
        status=job_update.status,
        error_message=job_update.error_message,
    )