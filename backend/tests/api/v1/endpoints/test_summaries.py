from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_summary_service
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


def _make_summary(**overrides):
    summary = MagicMock(name="summary")
    summary.id = overrides.get("id", 1)
    summary.video_id = overrides.get("video_id", 10)
    summary.type = overrides.get("type", "executive")
    summary.content = overrides.get("content", "The video covers deployment strategy.")
    summary.model_name = overrides.get("model_name", "qwen3:8b")
    summary.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    return summary


def test_summaries_endpoint_requires_authentication(client):
    response = client.get("/api/v1/summaries/video/10")

    assert response.status_code == 401


def test_summaries_endpoint_returns_summaries_for_owned_video(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    summary_service = MagicMock(name="summary_service")

    video_service.get_video.return_value = MagicMock(id=10)
    summary_service.get_by_video_id.return_value = [_make_summary(id=1)]

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_summary_service] = lambda: summary_service

    response = client.get("/api/v1/summaries/video/10")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["content"] == "The video covers deployment strategy."

    video_service.get_video.assert_called_once_with(video_id=10, user_id=99)
    summary_service.get_by_video_id.assert_called_once_with(video_id=10)


def test_summaries_endpoint_returns_empty_list_when_none_generated(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    summary_service = MagicMock(name="summary_service")

    video_service.get_video.return_value = MagicMock(id=10)
    summary_service.get_by_video_id.return_value = []

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_summary_service] = lambda: summary_service

    response = client.get("/api/v1/summaries/video/10")

    assert response.status_code == 200
    assert response.json() == []


def test_summaries_endpoint_video_not_owned_returns_404_and_skips_lookup(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    summary_service = MagicMock(name="summary_service")

    video_service.get_video.side_effect = HTTPException(
        status_code=404, detail="Video not found",
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_summary_service] = lambda: summary_service

    response = client.get("/api/v1/summaries/video/10")

    assert response.status_code == 404
    summary_service.get_by_video_id.assert_not_called()
