from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_storage_backend
from app.api.deps import get_video_service
from app.auth.dependencies import get_current_user_for_media
from app.main import app
from app.models.user import User


@pytest.fixture
def client():
    with TestClient(app, follow_redirects=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _make_user(user_id: int) -> User:
    return User(
        id=user_id,
        username="owner",
        email="owner@example.com",
        hashed_password="hashed",
    )


def test_stream_requires_authentication(client):
    response = client.get("/api/v1/videos/10/stream")

    assert response.status_code == 401


def test_stream_video_not_owned_returns_404_and_never_touches_storage(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    storage = MagicMock(name="storage")

    video_service.get_video.side_effect = HTTPException(
        status_code=404, detail="Video not found",
    )

    app.dependency_overrides[get_current_user_for_media] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_storage_backend] = lambda: storage

    response = client.get("/api/v1/videos/10/stream")

    assert response.status_code == 404
    storage.get_url.assert_not_called()
    storage.get_local_path.assert_not_called()


def test_stream_serves_local_file_when_backend_has_no_url(client, tmp_path):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    storage = MagicMock(name="storage")

    video = MagicMock(id=10, filename="clip.mp4")
    video_service.get_video.return_value = video

    real_file = tmp_path / "clip.mp4"
    real_file.write_bytes(b"fake mp4 bytes")

    storage.get_url.return_value = None
    storage.get_local_path.return_value = real_file

    app.dependency_overrides[get_current_user_for_media] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_storage_backend] = lambda: storage

    response = client.get("/api/v1/videos/10/stream")

    assert response.status_code == 200
    assert response.content == b"fake mp4 bytes"
    storage.get_url.assert_called_once_with("videos/clip.mp4")
    storage.get_local_path.assert_called_once_with("videos/clip.mp4")


def test_stream_redirects_to_presigned_url_when_backend_provides_one(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    storage = MagicMock(name="storage")

    video = MagicMock(id=10, filename="clip.mp4")
    video_service.get_video.return_value = video

    storage.get_url.return_value = "https://bucket.s3.example.com/videos/clip.mp4?sig=abc"

    app.dependency_overrides[get_current_user_for_media] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_storage_backend] = lambda: storage

    response = client.get("/api/v1/videos/10/stream")

    assert response.status_code == 307
    assert response.headers["location"] == "https://bucket.s3.example.com/videos/clip.mp4?sig=abc"
    storage.get_local_path.assert_not_called()


def test_stream_returns_404_when_file_missing_from_local_storage(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    storage = MagicMock(name="storage")

    video = MagicMock(id=10, filename="missing.mp4")
    video_service.get_video.return_value = video

    storage.get_url.return_value = None
    storage.get_local_path.return_value = None

    app.dependency_overrides[get_current_user_for_media] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_storage_backend] = lambda: storage

    response = client.get("/api/v1/videos/10/stream")

    assert response.status_code == 404
