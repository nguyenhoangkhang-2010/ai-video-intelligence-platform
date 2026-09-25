from unittest.mock import MagicMock

import pytest

from app.core.exceptions import InvalidJobStatusTransitionError
from app.services.processing_job import ProcessingJobService


def _service_with_job(current_status: str):
    repository = MagicMock(name="repository")
    job = MagicMock(name="job")
    job.status = current_status
    job.started_at = None
    repository.get_by_id.return_value = job
    repository.update.side_effect = lambda job: job

    return ProcessingJobService(repository), job


@pytest.mark.parametrize(
    "current_status,new_status",
    [
        ("PENDING", "RUNNING"),
        ("PENDING", "FAILED"),
        ("RUNNING", "COMPLETED"),
        ("RUNNING", "FAILED"),
    ],
)
def test_update_job_status_allows_valid_transitions(current_status, new_status):
    service, job = _service_with_job(current_status)

    result = service.update_job_status(job_id=1, status=new_status)

    assert result.status == new_status


@pytest.mark.parametrize(
    "current_status,new_status",
    [
        ("COMPLETED", "PENDING"),
        ("COMPLETED", "RUNNING"),
        ("COMPLETED", "FAILED"),
        ("FAILED", "PENDING"),
        ("FAILED", "RUNNING"),
        ("FAILED", "COMPLETED"),
        ("PENDING", "COMPLETED"),  # cannot skip RUNNING
        ("RUNNING", "PENDING"),  # cannot go backwards
    ],
)
def test_update_job_status_rejects_invalid_transitions(current_status, new_status):
    service, job = _service_with_job(current_status)

    with pytest.raises(InvalidJobStatusTransitionError):
        service.update_job_status(job_id=1, status=new_status)

    # The job's status must be left untouched on a rejected transition.
    assert job.status == current_status


def test_update_job_status_raises_404_for_unknown_job():
    from fastapi import HTTPException

    repository = MagicMock(name="repository")
    repository.get_by_id.return_value = None
    service = ProcessingJobService(repository)

    with pytest.raises(HTTPException) as exc_info:
        service.update_job_status(job_id=999, status="RUNNING")

    assert exc_info.value.status_code == 404
