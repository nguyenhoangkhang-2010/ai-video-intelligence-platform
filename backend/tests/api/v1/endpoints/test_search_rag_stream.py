"""
POST /api/v1/search/videos/{video_id}/rag/stream - the streaming
(Server-Sent Events) variant of the grounded RAG answer.

Locks in the event contract the frontend relies on: `sources` first
(only when there is an answer to generate), then `token` pieces, then
exactly one terminal `done` carrying the same RAGResult shape as the
non-streaming endpoint - including `generation_failed` when the model
fails mid-answer.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from ai.llm.errors import LLMTimeoutError
from app.api.deps import get_rag_pipeline
from app.api.deps import get_video_service
from app.api.v1.endpoints import search as search_endpoint
from app.auth.dependencies import get_current_user
from app.main import app
from app.models.user import User
from app.pipelines.rag_pipeline import PreparedAnswer
from app.schemas.rag import RAGResult
from app.schemas.search import SearchResult


URL = "/api/v1/search/videos/10/rag/stream"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _user() -> User:
    return User(id=99, username="owner", email="owner@example.com", hashed_password="x")


def _source() -> SearchResult:
    return SearchResult(
        vector_id="v-1",
        video_id=10,
        chunk_index=3,
        chunk_text="Lạm phát là mức tăng chung của giá cả.",
        distance=0.12,
    )


def _prepared(pieces=None, error: Exception | None = None) -> PreparedAnswer:
    answerer = MagicMock(name="answerer")

    def stream(query, context):
        for piece in pieces or []:
            yield piece
        if error is not None:
            raise error

    answerer.answer_stream.side_effect = stream
    return PreparedAnswer(
        video_id=10,
        query="Lạm phát là gì?",
        context="[Source 1] ...",
        sources=[_source()],
        answerer=answerer,
    )


def _override(prepared):
    video_service = MagicMock(name="video_service")
    video_service.get_video.return_value = MagicMock(id=10)
    rag_pipeline = MagicMock(name="rag_pipeline")
    rag_pipeline.prepare.return_value = prepared

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_rag_pipeline] = lambda: rag_pipeline
    return video_service, rag_pipeline


def _events(response) -> list[tuple[str, dict]]:
    events = []
    for frame in response.text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in frame.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def test_streams_sources_then_tokens_then_done_and_records_history(client):
    video_service, rag_pipeline = _override(_prepared(["Lạm phát ", "là mức tăng ", "giá cả."]))

    with patch.object(search_endpoint, "_record_chat_history") as record:
        response = client.post(URL, json={"query": "Lạm phát là gì?", "top_k": 3})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-accel-buffering"] == "no"

    events = _events(response)
    names = [name for name, _ in events]
    assert names == ["sources", "token", "token", "token", "done"]

    assert events[0][1]["sources"][0]["chunk_index"] == 3
    assert "".join(data["text"] for name, data in events if name == "token") == (
        "Lạm phát là mức tăng giá cả."
    )

    done = events[-1][1]
    assert done["status"] == "answered"
    assert done["answer"] == "Lạm phát là mức tăng giá cả."
    assert done["sources"][0]["vector_id"] == "v-1"

    video_service.get_video.assert_called_once_with(video_id=10, user_id=99)
    rag_pipeline.prepare.assert_called_once_with(video_id=10, query="Lạm phát là gì?", top_k=3)
    record.assert_called_once()
    assert record.call_args.kwargs["answer"] == "Lạm phát là mức tăng giá cả."
    assert record.call_args.kwargs["user_id"] == 99


def test_failure_mid_answer_ends_with_generation_failed_and_records_nothing(client):
    _override(_prepared(["Lạm phát "], error=LLMTimeoutError("stalled")))

    with patch.object(search_endpoint, "_record_chat_history") as record:
        response = client.post(URL, json={"query": "Lạm phát là gì?"})

    events = _events(response)
    assert [name for name, _ in events] == ["sources", "token", "done"]
    assert events[-1][1]["status"] == "generation_failed"
    assert events[-1][1]["answer"] is None
    record.assert_not_called()


def test_whitespace_only_answer_is_treated_as_generation_failed(client):
    _override(_prepared(["  ", "\n"]))

    with patch.object(search_endpoint, "_record_chat_history") as record:
        response = client.post(URL, json={"query": "Lạm phát là gì?"})

    assert _events(response)[-1][1]["status"] == "generation_failed"
    record.assert_not_called()


def test_nothing_to_ground_in_sends_only_done_without_calling_the_llm(client):
    _override(
        RAGResult(video_id=10, query="xyz", status="no_relevant_chunks", sources=[]),
    )

    response = client.post(URL, json={"query": "xyz"})

    events = _events(response)
    assert [name for name, _ in events] == ["done"]
    assert events[0][1]["status"] == "no_relevant_chunks"


def test_video_not_owned_is_a_normal_404_before_streaming_starts(client):
    video_service, rag_pipeline = _override(_prepared(["x"]))
    video_service.get_video.side_effect = HTTPException(status_code=404, detail="Video not found")

    response = client.post(URL, json={"query": "anything"})

    assert response.status_code == 404
    rag_pipeline.prepare.assert_not_called()


def test_unauthenticated_request_is_rejected(client):
    response = client.post(URL, json={"query": "anything"})

    assert response.status_code == 401
