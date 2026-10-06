from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_quiz_service
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


def _make_quiz(**overrides):
    quiz = MagicMock(name="quiz")
    quiz.id = overrides.get("id", 1)
    quiz.video_id = overrides.get("video_id", 10)
    quiz.type = overrides.get("type", "mcq")
    quiz.question = overrides.get("question", "What is the main topic?")
    quiz.answer = overrides.get("answer", "Deployment strategy")
    quiz.options = overrides.get("options", None)
    return quiz


def test_quizzes_endpoint_requires_authentication(client):
    response = client.get("/api/v1/videos/10/quizzes")

    assert response.status_code == 401


def test_quizzes_endpoint_returns_quizzes_for_owned_video(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    quiz_service = MagicMock(name="quiz_service")

    video_service.get_video.return_value = MagicMock(id=10)
    quiz_service.get_by_video_id.return_value = [
        _make_quiz(id=1, type="mcq"),
        _make_quiz(id=2, type="true_false", question="Is this correct?", answer="true"),
    ]

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_quiz_service] = lambda: quiz_service

    response = client.get("/api/v1/videos/10/quizzes")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["type"] == "mcq"
    assert body[1]["type"] == "true_false"

    video_service.get_video.assert_called_once_with(video_id=10, user_id=99)
    quiz_service.get_by_video_id.assert_called_once_with(video_id=10)


def test_quizzes_endpoint_returns_empty_list_when_none_generated(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    quiz_service = MagicMock(name="quiz_service")

    video_service.get_video.return_value = MagicMock(id=10)
    quiz_service.get_by_video_id.return_value = []

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_quiz_service] = lambda: quiz_service

    response = client.get("/api/v1/videos/10/quizzes")

    assert response.status_code == 200
    assert response.json() == []


def test_quizzes_endpoint_video_not_owned_returns_404_and_skips_lookup(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    quiz_service = MagicMock(name="quiz_service")

    video_service.get_video.side_effect = HTTPException(
        status_code=404, detail="Video not found",
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_quiz_service] = lambda: quiz_service

    response = client.get("/api/v1/videos/10/quizzes")

    assert response.status_code == 404
    quiz_service.get_by_video_id.assert_not_called()
