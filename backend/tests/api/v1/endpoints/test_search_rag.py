from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_rag_pipeline
from app.api.deps import get_video_service
from app.auth.dependencies import get_current_user
from app.main import app
from app.models.user import User
from app.schemas.rag import RAGResult


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


def test_rag_endpoint_unauthenticated_request_is_rejected(client):
    # No Authorization header, get_current_user is NOT overridden -
    # exercises the real auth dependency chain.
    response = client.post(
        "/api/v1/search/videos/10/rag",
        json={"query": "what is this about?"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_rag_endpoint_owned_video_calls_pipeline_with_forwarded_arguments(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    rag_pipeline = MagicMock(name="rag_pipeline")

    video_service.get_video.return_value = MagicMock(id=10)
    rag_pipeline.ask.return_value = RAGResult(
        video_id=10,
        query="what is this about?",
        status="answered",
        answer="It's about X.",
        sources=[],
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_rag_pipeline] = lambda: rag_pipeline

    response = client.post(
        "/api/v1/search/videos/10/rag",
        json={"query": "what is this about?", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["video_id"] == 10
    assert body["query"] == "what is this about?"
    assert body["status"] == "answered"
    assert body["answer"] == "It's about X."

    # Ownership checked (video_id + the CURRENT user's id) before the
    # RAG pipeline is ever touched.
    video_service.get_video.assert_called_once_with(video_id=10, user_id=99)

    # video_id, query (unchanged), and top_k (non-default value, to
    # prove it is genuinely forwarded and not just defaulted) all
    # reach RAGPipeline.ask() via the injected get_rag_pipeline
    # dependency.
    rag_pipeline.ask.assert_called_once_with(
        video_id=10,
        query="what is this about?",
        top_k=3,
    )


def test_rag_endpoint_video_not_owned_returns_404_and_never_calls_pipeline(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    rag_pipeline = MagicMock(name="rag_pipeline")

    # Matches the actual VideoService.get_video() behavior for both
    # "not found" and "not owned by this user".
    video_service.get_video.side_effect = HTTPException(
        status_code=404,
        detail="Video not found",
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_rag_pipeline] = lambda: rag_pipeline

    response = client.post(
        "/api/v1/search/videos/10/rag",
        json={"query": "what is this about?"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Video not found"

    rag_pipeline.ask.assert_not_called()


def test_rag_endpoint_terminal_status_is_returned_as_200_not_an_error(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    rag_pipeline = MagicMock(name="rag_pipeline")

    video_service.get_video.return_value = MagicMock(id=10)
    rag_pipeline.ask.return_value = RAGResult(
        video_id=10,
        query="anything relevant?",
        status="no_relevant_chunks",
        sources=[],
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_rag_pipeline] = lambda: rag_pipeline

    response = client.post(
        "/api/v1/search/videos/10/rag",
        json={"query": "anything relevant?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_relevant_chunks"
    assert body["answer"] is None
    assert body["sources"] == []
