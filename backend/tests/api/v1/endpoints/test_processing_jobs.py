from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_processing_job_service
from app.auth.dependencies import get_current_user
from app.main import app
from app.models.user import User


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _make_user(user_id: int) -> User:
    return User(
        id=user_id,
        username="owner",
        email="owner@example.com",
        hashed_password="hashed",
    )


def _make_job(**overrides):
    job = MagicMock(name="job")
    job.id = overrides.get("id", 1)
    job.video_id = overrides.get("video_id", 10)
    job.job_type = overrides.get("job_type", "transcription")
    job.status = overrides.get("status", "PENDING")
    job.progress = overrides.get("progress", 0)
    job.current_step = overrides.get("current_step", None)
    job.started_at = overrides.get("started_at", None)
    job.finished_at = overrides.get("finished_at", None)
    job.error_message = overrides.get("error_message", None)
    return job


def test_list_processing_jobs_requires_authentication(client):
    response = client.get("/api/v1/processing-jobs")

    assert response.status_code == 401


def test_list_processing_jobs_is_scoped_to_current_user(client):
    """
    Previously this endpoint returned ALL jobs for ALL users - the
    fix must call the ownership-scoped service method with the
    current user's id, not the unscoped one.
    """
    current_user = _make_user(user_id=99)
    service = MagicMock(name="service")
    service.get_jobs_for_user.return_value = [_make_job(id=1), _make_job(id=2)]

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_processing_job_service] = lambda: service

    response = client.get("/api/v1/processing-jobs")

    assert response.status_code == 200
    assert len(response.json()) == 2
    service.get_jobs_for_user.assert_called_once_with(user_id=99)
    service.get_all_jobs.assert_not_called()


def test_get_processing_job_requires_authentication(client):
    response = client.get("/api/v1/processing-jobs/1")

    assert response.status_code == 401


def test_get_processing_job_uses_ownership_scoped_lookup(client):
    current_user = _make_user(user_id=99)
    service = MagicMock(name="service")
    service.get_job_for_user.return_value = _make_job(id=1)

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_processing_job_service] = lambda: service

    response = client.get("/api/v1/processing-jobs/1")

    assert response.status_code == 200
    service.get_job_for_user.assert_called_once_with(job_id=1, user_id=99)
    service.get_job.assert_not_called()


def test_get_processing_job_not_owned_returns_404():
    """
    get_job_for_user itself raises 404 for a job that doesn't belong
    to the caller - verified directly against the real service logic
    in tests/repositories/test_processing_job_repository.py; here we
    only need the endpoint to propagate whatever the service raises.
    """
    from fastapi import HTTPException

    with TestClient(app) as client:
        current_user = _make_user(user_id=99)
        service = MagicMock(name="service")
        service.get_job_for_user.side_effect = HTTPException(
            status_code=404, detail="Processing job not found",
        )

        app.dependency_overrides[get_current_user] = lambda: current_user
        app.dependency_overrides[get_processing_job_service] = lambda: service

        response = client.get("/api/v1/processing-jobs/1")

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_patch_processing_job_requires_authentication(client):
    response = client.patch(
        "/api/v1/processing-jobs/1", json={"status": "COMPLETED"},
    )

    assert response.status_code == 401


def test_patch_processing_job_verifies_ownership_before_mutating(client):
    current_user = _make_user(user_id=99)
    service = MagicMock(name="service")
    service.get_job_for_user.return_value = _make_job(id=1)
    service.update_job_status.return_value = _make_job(id=1, status="COMPLETED")

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_processing_job_service] = lambda: service

    response = client.patch(
        "/api/v1/processing-jobs/1", json={"status": "COMPLETED"},
    )

    assert response.status_code == 200
    service.get_job_for_user.assert_called_once_with(job_id=1, user_id=99)
    service.update_job_status.assert_called_once_with(
        job_id=1, status="COMPLETED", error_message=None,
    )


def test_patch_processing_job_not_owned_returns_404_and_never_mutates(client):
    from fastapi import HTTPException

    current_user = _make_user(user_id=99)
    service = MagicMock(name="service")
    service.get_job_for_user.side_effect = HTTPException(
        status_code=404, detail="Processing job not found",
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_processing_job_service] = lambda: service

    response = client.patch(
        "/api/v1/processing-jobs/1", json={"status": "COMPLETED"},
    )

    assert response.status_code == 404
    service.update_job_status.assert_not_called()
