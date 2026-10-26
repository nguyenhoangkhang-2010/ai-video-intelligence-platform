from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
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


def test_semantic_search_requires_authentication(client):
    """
    Previously this endpoint had no authentication/ownership check at
    all - any caller could search any video's content by id.
    """
    response = client.post(
        "/api/v1/search/videos/10", json={"query": "hello"},
    )

    assert response.status_code == 401


def test_semantic_search_checks_ownership_before_searching(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    video_service.get_video.return_value = MagicMock(id=10)

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service

    with patch(
        "app.api.v1.endpoints.search.SemanticSearchService",
    ) as mock_service_cls:
        mock_service_cls.return_value.search.return_value = []

        response = client.post(
            "/api/v1/search/videos/10", json={"query": "hello", "top_k": 3},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["video_id"] == 10
    assert body["query"] == "hello"
    assert body["results"] == []

    video_service.get_video.assert_called_once_with(video_id=10, user_id=99)
    mock_service_cls.return_value.search.assert_called_once_with(
        video_id=10, query="hello", top_k=3,
    )


def test_semantic_search_video_not_owned_returns_404_and_never_searches(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    video_service.get_video.side_effect = HTTPException(
        status_code=404, detail="Video not found",
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service

    with patch(
        "app.api.v1.endpoints.search.SemanticSearchService",
    ) as mock_service_cls:
        response = client.post(
            "/api/v1/search/videos/10", json={"query": "hello"},
        )

    assert response.status_code == 404
    mock_service_cls.return_value.search.assert_not_called()
