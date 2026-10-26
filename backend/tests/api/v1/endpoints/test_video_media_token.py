from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_video_service
from app.auth.dependencies import get_current_user
from app.auth.jwt import decode_token
from app.config.settings import settings
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


def test_media_token_requires_authentication(client):
    response = client.get("/api/v1/videos/10/media-token")

    assert response.status_code == 401


def test_media_token_not_owned_returns_404_and_mints_nothing(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    video_service.get_video.side_effect = HTTPException(
        status_code=404, detail="Video not found",
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service

    response = client.get("/api/v1/videos/10/media-token")

    assert response.status_code == 404


def test_media_token_returns_scoped_token_for_owner(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    video_service.get_video.return_value = MagicMock(id=10)

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service

    response = client.get("/api/v1/videos/10/media-token")

    assert response.status_code == 200
    body = response.json()
    assert body["expires_in"] == settings.security.media_token_expire_seconds

    payload = decode_token(body["token"])
    assert payload["scope"] == "media"
    assert payload["video_id"] == 10
    assert payload["sub"] == "99"

    video_service.get_video.assert_called_once_with(video_id=10, user_id=99)


def test_media_token_is_not_the_callers_access_token(client):
    """
    The token returned here must never equal (or be derivable as) the
    caller's own long-lived access token - it's a distinct, narrowly
    scoped credential minted fresh for this video.
    """
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    video_service.get_video.return_value = MagicMock(id=10)

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service

    response = client.get("/api/v1/videos/10/media-token")
    token = response.json()["token"]

    payload = decode_token(token)
    assert "video_id" in payload
    assert payload["scope"] == "media"
