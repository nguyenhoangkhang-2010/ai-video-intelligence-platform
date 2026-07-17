from fastapi import APIRouter
from fastapi import Depends

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
    service: ProcessingJobService = Depends(
        get_processing_job_service,
    ),
):
    """
    Get all processing jobs.
    """
    return service.get_all_jobs()

@router.get(
    "/{job_id}",
    response_model=ProcessingJobRead,
)
def get_processing_job(
    job_id: int,
    service: ProcessingJobService = Depends(
        get_processing_job_service,
    ),
):
    """
    Get processing job by ID.
    """
    return service.get_job(
        job_id=job_id,
    )
    
@router.patch(
    "/{job_id}",
    response_model=ProcessingJobRead,
)
def update_processing_job(
    job_id: int,
    job_update: ProcessingJobStatusUpdate,
    service: ProcessingJobService = Depends(
        get_processing_job_service,
    ),
):
    """
    Update processing job status.
    """
    return service.update_job_status(
        job_id=job_id,
        status=job_update.status,
        error_message=job_update.error_message,
    )