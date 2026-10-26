"""
Streaming generation: OllamaClient.generate_stream and
RagAnswerer.answer_stream. No real Ollama - requests.post is patched
to return a fake streaming response.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from ai.llm.errors import (
    LLMConnectionError,
    LLMEmptyResponseError,
    LLMMalformedResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from ai.llm.ollama_client import OllamaClient
from ai.llm.rag_answerer import RagAnswerer


def _streaming_response(lines, status_code=200, error_after=None):
    response = MagicMock(name="response")
    response.status_code = status_code
    response.__enter__.return_value = response
    response.__exit__.return_value = False

    if status_code >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError("bad status")

    def iter_lines(decode_unicode=True):
        for line in lines:
            yield line
        if error_after is not None:
            raise error_after

    response.iter_lines.side_effect = iter_lines
    return response


def _ndjson(*objects):
    return [json.dumps(obj) for obj in objects]


def _client():
    return OllamaClient(base_url="http://ollama.test", model="test-model")


def test_generate_stream_yields_response_pieces_until_done():
    lines = _ndjson(
        {"response": "Lạm ", "done": False},
        {"response": "phát", "done": False, "thinking": "ignored"},
        {"response": "", "done": True},
        {"response": "after done is never read", "done": False},
    )
    with patch("ai.llm.ollama_client.requests.post", return_value=_streaming_response(lines)) as post:
        pieces = list(_client().generate_stream("prompt"))

    assert pieces == ["Lạm ", "phát"]
    kwargs = post.call_args.kwargs
    assert kwargs["json"]["stream"] is True
    assert kwargs["stream"] is True


def test_generate_stream_skips_blank_keepalive_lines():
    lines = ["", *_ndjson({"response": "ok", "done": True})]
    with patch("ai.llm.ollama_client.requests.post", return_value=_streaming_response(lines)):
        assert list(_client().generate_stream("prompt")) == ["ok"]


def test_generate_stream_maps_http_error_status():
    with patch(
        "ai.llm.ollama_client.requests.post",
        return_value=_streaming_response([], status_code=500),
    ):
        with pytest.raises(LLMUnavailableError):
            list(_client().generate_stream("prompt"))


def test_generate_stream_maps_an_error_object_in_the_stream():
    lines = _ndjson({"error": "model failed to load"})
    with patch("ai.llm.ollama_client.requests.post", return_value=_streaming_response(lines)):
        with pytest.raises(LLMUnavailableError, match="model failed to load"):
            list(_client().generate_stream("prompt"))


def test_generate_stream_rejects_a_malformed_line():
    with patch(
        "ai.llm.ollama_client.requests.post",
        return_value=_streaming_response(["{not json"]),
    ):
        with pytest.raises(LLMMalformedResponseError):
            list(_client().generate_stream("prompt"))


def test_generate_stream_with_no_text_at_all_is_an_empty_response():
    lines = _ndjson({"response": "", "done": True})
    with patch("ai.llm.ollama_client.requests.post", return_value=_streaming_response(lines)):
        with pytest.raises(LLMEmptyResponseError):
            list(_client().generate_stream("prompt"))


def test_generate_stream_maps_a_stall_mid_answer_to_a_timeout():
    lines = _ndjson({"response": "partial", "done": False})
    response = _streaming_response(lines, error_after=requests.exceptions.ReadTimeout("stalled"))
    with patch("ai.llm.ollama_client.requests.post", return_value=response):
        stream = _client().generate_stream("prompt")
        assert next(stream) == "partial"
        with pytest.raises(LLMTimeoutError):
            next(stream)


def test_generate_stream_maps_a_dropped_connection_mid_answer():
    lines = _ndjson({"response": "partial", "done": False})
    response = _streaming_response(
        lines, error_after=requests.exceptions.ChunkedEncodingError("connection reset"),
    )
    with patch("ai.llm.ollama_client.requests.post", return_value=response):
        with pytest.raises(LLMConnectionError):
            list(_client().generate_stream("prompt"))


def test_generate_stream_maps_an_unreachable_server():
    with patch(
        "ai.llm.ollama_client.requests.post",
        side_effect=requests.exceptions.ConnectionError("refused"),
    ), patch("time.sleep"):
        with pytest.raises(LLMConnectionError):
            list(_client().generate_stream("prompt"))


# --- RagAnswerer.answer_stream ----------------------------------------------


class _StreamingProvider:
    def generate(self, prompt):
        raise AssertionError("streaming provider should be streamed, not generated")

    def generate_stream(self, prompt):
        yield "Một "
        yield "câu trả lời."


class _PlainProvider:
    def generate(self, prompt):
        return "Câu trả lời đầy đủ."


def test_answer_stream_streams_from_a_streaming_provider():
    answerer = RagAnswerer(llm_client=_StreamingProvider())

    assert list(answerer.answer_stream("Hỏi?", "Ngữ cảnh")) == ["Một ", "câu trả lời."]


def test_answer_stream_falls_back_to_one_piece_for_a_non_streaming_provider():
    answerer = RagAnswerer(llm_client=_PlainProvider())

    assert list(answerer.answer_stream("Hỏi?", "Ngữ cảnh")) == ["Câu trả lời đầy đủ."]


@pytest.mark.parametrize("query,context", [("", "ctx"), ("   ", "ctx"), ("q", ""), ("q", "  ")])
def test_answer_stream_validates_before_streaming(query, context):
    answerer = RagAnswerer(llm_client=_PlainProvider())

    with pytest.raises(ValueError):
        answerer.answer_stream(query, context)
