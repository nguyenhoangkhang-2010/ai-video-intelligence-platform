from fastapi import APIRouter
from fastapi import Depends

from app.api.deps import get_processing_job_service
from app.services.processing_job import ProcessingJobService
from app.schemas.processing_job import ProcessingJobRead

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