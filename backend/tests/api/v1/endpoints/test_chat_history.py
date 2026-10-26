from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_chat_history_service
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


def _make_entry(**overrides):
    entry = MagicMock(name="chat_history")
    entry.id = overrides.get("id", 1)
    entry.user_id = overrides.get("user_id", 99)
    entry.video_id = overrides.get("video_id", 10)
    entry.question = overrides.get("question", "What is this video about?")
    entry.answer = overrides.get("answer", "It covers deployment strategy.")
    entry.sources = overrides.get("sources", [])
    entry.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    return entry


def test_chat_history_endpoint_requires_authentication(client):
    response = client.get("/api/v1/videos/10/chat-history")

    assert response.status_code == 401


def test_chat_history_endpoint_returns_this_users_own_turns(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    chat_history_service = MagicMock(name="chat_history_service")

    video_service.get_video.return_value = MagicMock(id=10)
    chat_history_service.get_by_user_and_video.return_value = [
        _make_entry(id=1, question="First question?"),
    ]

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_chat_history_service] = lambda: chat_history_service

    response = client.get("/api/v1/videos/10/chat-history")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["question"] == "First question?"
    assert body[0]["user_id"] == 99

    video_service.get_video.assert_called_once_with(video_id=10, user_id=99)
    # Scoped by both user_id and video_id - never just video_id - so
    # one user's chat history is never returned for another user on
    # the same video.
    chat_history_service.get_by_user_and_video.assert_called_once_with(
        user_id=99, video_id=10,
    )


def test_chat_history_endpoint_returns_empty_list_when_no_turns_yet(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    chat_history_service = MagicMock(name="chat_history_service")

    video_service.get_video.return_value = MagicMock(id=10)
    chat_history_service.get_by_user_and_video.return_value = []

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_chat_history_service] = lambda: chat_history_service

    response = client.get("/api/v1/videos/10/chat-history")

    assert response.status_code == 200
    assert response.json() == []


def test_chat_history_endpoint_video_not_owned_returns_404_and_skips_lookup(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    chat_history_service = MagicMock(name="chat_history_service")

    video_service.get_video.side_effect = HTTPException(
        status_code=404, detail="Video not found",
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_chat_history_service] = lambda: chat_history_service

    response = client.get("/api/v1/videos/10/chat-history")

    assert response.status_code == 404
    chat_history_service.get_by_user_and_video.assert_not_called()
