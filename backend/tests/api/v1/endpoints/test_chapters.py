from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_chapter_service
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


def _make_chapter(**overrides):
    chapter = MagicMock(name="chapter")
    chapter.id = overrides.get("id", 1)
    chapter.video_id = overrides.get("video_id", 10)
    chapter.title = overrides.get("title", "Introduction")
    chapter.start_time = overrides.get("start_time", 0.0)
    chapter.end_time = overrides.get("end_time", 30.0)
    chapter.summary = overrides.get("summary", "An intro segment.")
    return chapter


def test_chapters_endpoint_requires_authentication(client):
    response = client.get("/api/v1/videos/10/chapters")

    assert response.status_code == 401


def test_chapters_endpoint_returns_ordered_chapters_for_owned_video(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    chapter_service = MagicMock(name="chapter_service")

    video_service.get_video.return_value = MagicMock(id=10)
    chapter_service.get_by_video_id.return_value = [
        _make_chapter(id=1, start_time=0.0, end_time=30.0),
        _make_chapter(id=2, start_time=30.0, end_time=90.0, title="Deep dive"),
    ]

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_chapter_service] = lambda: chapter_service

    response = client.get("/api/v1/videos/10/chapters")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["title"] == "Introduction"
    assert body[1]["title"] == "Deep dive"

    video_service.get_video.assert_called_once_with(video_id=10, user_id=99)
    chapter_service.get_by_video_id.assert_called_once_with(video_id=10)


def test_chapters_endpoint_returns_empty_list_when_none_detected(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    chapter_service = MagicMock(name="chapter_service")

    video_service.get_video.return_value = MagicMock(id=10)
    chapter_service.get_by_video_id.return_value = []

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_chapter_service] = lambda: chapter_service

    response = client.get("/api/v1/videos/10/chapters")

    assert response.status_code == 200
    assert response.json() == []


def test_chapters_endpoint_video_not_owned_returns_404_and_skips_lookup(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    chapter_service = MagicMock(name="chapter_service")

    video_service.get_video.side_effect = HTTPException(
        status_code=404, detail="Video not found",
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_chapter_service] = lambda: chapter_service

    response = client.get("/api/v1/videos/10/chapters")

    assert response.status_code == 404
    chapter_service.get_by_video_id.assert_not_called()
