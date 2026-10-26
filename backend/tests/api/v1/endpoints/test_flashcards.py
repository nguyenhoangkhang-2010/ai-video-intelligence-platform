from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_flashcard_service
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


def _make_flashcard(**overrides):
    flashcard = MagicMock(name="flashcard")
    flashcard.id = overrides.get("id", 1)
    flashcard.video_id = overrides.get("video_id", 10)
    flashcard.question = overrides.get("question", "What is X?")
    flashcard.answer = overrides.get("answer", "X is Y.")
    flashcard.difficulty = overrides.get("difficulty", "medium")
    return flashcard


def test_flashcards_endpoint_requires_authentication(client):
    response = client.get("/api/v1/videos/10/flashcards")

    assert response.status_code == 401


def test_flashcards_endpoint_returns_flashcards_for_owned_video(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    flashcard_service = MagicMock(name="flashcard_service")

    video_service.get_video.return_value = MagicMock(id=10)
    flashcard_service.get_by_video_id.return_value = [
        _make_flashcard(id=1, question="Q1?", answer="A1"),
        _make_flashcard(id=2, question="Q2?", answer="A2"),
    ]

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_flashcard_service] = lambda: flashcard_service

    response = client.get("/api/v1/videos/10/flashcards")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["question"] == "Q1?"

    video_service.get_video.assert_called_once_with(video_id=10, user_id=99)


def test_flashcards_endpoint_video_not_owned_returns_404(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    flashcard_service = MagicMock(name="flashcard_service")

    video_service.get_video.side_effect = HTTPException(
        status_code=404, detail="Video not found",
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_flashcard_service] = lambda: flashcard_service

    response = client.get("/api/v1/videos/10/flashcards")

    assert response.status_code == 404
    flashcard_service.get_by_video_id.assert_not_called()


def test_flashcards_export_requires_authentication(client):
    response = client.get("/api/v1/videos/10/flashcards/export")

    assert response.status_code == 401


def test_flashcards_export_returns_utf8_tsv_with_content_disposition(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    flashcard_service = MagicMock(name="flashcard_service")

    video_service.get_video.return_value = MagicMock(id=10)
    flashcard_service.get_by_video_id.return_value = [
        _make_flashcard(question="Front unicode: đ", answer="Back unicode: ệ"),
    ]

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_flashcard_service] = lambda: flashcard_service

    response = client.get("/api/v1/videos/10/flashcards/export")

    assert response.status_code == 200
    assert "tab-separated-values" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert "video-10-flashcards.tsv" in response.headers["content-disposition"]
    assert response.text == "Front unicode: đ\tBack unicode: ệ"


def test_flashcards_export_handles_empty_flashcard_list(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    flashcard_service = MagicMock(name="flashcard_service")

    video_service.get_video.return_value = MagicMock(id=10)
    flashcard_service.get_by_video_id.return_value = []

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_flashcard_service] = lambda: flashcard_service

    response = client.get("/api/v1/videos/10/flashcards/export")

    assert response.status_code == 200
    assert response.text == ""
