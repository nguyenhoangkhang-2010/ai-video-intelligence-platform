from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_transcript_service
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


def test_get_transcript_requires_authentication(client):
    """
    Previously this endpoint had no authentication/ownership check at
    all - any caller could read any video's transcript by id.
    """
    response = client.get("/api/v1/transcripts/10")

    assert response.status_code == 401


def test_get_transcript_checks_ownership_before_returning_transcript(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    transcript_service = MagicMock(name="transcript_service")

    video_service.get_video.return_value = MagicMock(id=10)
    transcript = MagicMock()
    transcript.id = 1
    transcript.video_id = 10
    transcript.language = "en"
    transcript.text = "hello world"
    transcript.word_count = 2
    transcript_service.get_by_video_id.return_value = transcript

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_transcript_service] = lambda: transcript_service

    response = client.get("/api/v1/transcripts/10")

    assert response.status_code == 200
    assert response.json()["text"] == "hello world"
    video_service.get_video.assert_called_once_with(video_id=10, user_id=99)


def test_get_transcript_video_not_owned_returns_404_and_skips_lookup(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    transcript_service = MagicMock(name="transcript_service")

    video_service.get_video.side_effect = HTTPException(
        status_code=404, detail="Video not found",
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_transcript_service] = lambda: transcript_service

    response = client.get("/api/v1/transcripts/10")

    assert response.status_code == 404
    transcript_service.get_by_video_id.assert_not_called()


def test_get_transcript_returns_404_when_transcript_not_yet_generated(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    transcript_service = MagicMock(name="transcript_service")

    video_service.get_video.return_value = MagicMock(id=10)
    transcript_service.get_by_video_id.return_value = None

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_transcript_service] = lambda: transcript_service

    response = client.get("/api/v1/transcripts/10")

    assert response.status_code == 404
    assert response.json()["detail"] == "Transcript not found"
