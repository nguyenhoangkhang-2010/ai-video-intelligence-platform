from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_video_service
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


def _make_video(**overrides):
    video = MagicMock(name="video")
    video.id = overrides.get("id", 1)
    video.owner_id = overrides.get("owner_id", 99)
    video.title = overrides.get("title", "clip.mp4")
    video.filename = overrides.get("filename", "abc_clip.mp4")
    video.language = overrides.get("language", "en")
    video.duration = overrides.get("duration", 42)
    video.status = overrides.get("status", "processed")
    return video


def test_put_video_accepts_a_real_status_value(client):
    current_user = _make_user(user_id=99)
    service = MagicMock(name="video_service")
    service.update_video.return_value = _make_video(status="failed")

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: service

    response = client.put(
        "/api/v1/videos/1", json={"status": "failed"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_put_video_rejects_a_status_value_outside_the_known_enum(client):
    """
    VideoUpdate.status is now a Literal of the 4 real Video.status
    values - a client can no longer self-assign an arbitrary status
    string (e.g. spoofing "processed" without real processing).
    """
    current_user = _make_user(user_id=99)
    service = MagicMock(name="video_service")

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: service

    response = client.put(
        "/api/v1/videos/1", json={"status": "definitely-not-real"},
    )

    assert response.status_code == 422
    service.update_video.assert_not_called()
