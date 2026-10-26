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


def _client():
    return OllamaClient(base_url="http://ollama.test", model="test-model")


def _ok_response(text="a real answer"):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"response": text}
    return response


def test_generate_returns_response_text_on_success():
    with patch("ai.llm.ollama_client.requests.post", return_value=_ok_response("hello")) as post:
        result = _client().generate("prompt")

    assert result == "hello"
    post.assert_called_once()


def test_generate_raises_llm_empty_response_error_without_retrying():
    with patch("ai.llm.ollama_client.requests.post", return_value=_ok_response("")) as post:
        with pytest.raises(LLMEmptyResponseError):
            _client().generate("prompt")

    # An empty-but-well-formed response is an application-level
    # condition, not a transient failure - retrying the identical
    # prompt is not expected to help, so this must not be retried.
    assert post.call_count == 1


def test_generate_raises_llm_malformed_response_error_on_invalid_json():
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.side_effect = ValueError("not json")

    with patch("ai.llm.ollama_client.requests.post", return_value=response) as post:
        with pytest.raises(LLMMalformedResponseError):
            _client().generate("prompt")

    assert post.call_count == 1


def test_generate_retries_on_connection_error():
    with patch(
        "ai.llm.ollama_client.requests.post",
        side_effect=[requests.exceptions.ConnectionError("refused"), _ok_response("second try")],
    ) as post, patch("ai.llm.ollama_client.wait_exponential", return_value=lambda *a, **k: 0):
        result = _client().generate("prompt")

    assert result == "second try"
    assert post.call_count == 2


def test_generate_raises_llm_connection_error_after_retries_exhausted():
    with patch(
        "ai.llm.ollama_client.requests.post",
        side_effect=requests.exceptions.ConnectionError("refused"),
    ) as post, patch("ai.llm.ollama_client.wait_exponential", return_value=lambda *a, **k: 0):
        with pytest.raises(LLMConnectionError):
            _client().generate("prompt")

    # Bounded: the existing retry policy caps this at 3 attempts.
    assert post.call_count == 3


def test_generate_raises_llm_timeout_error_without_retrying():
    """
    A Timeout means Ollama accepted the request and was still
    generating when the client gave up - the response was genuinely
    slow, not broken. Retrying an identical prompt is expected to be
    just as slow again, so this must raise immediately instead of
    stacking another full-length wait on top (this exact behavior was
    observed live: one slow-but-successful generation compounding into
    a multi-minute hang before this fix).
    """
    with patch(
        "ai.llm.ollama_client.requests.post",
        side_effect=requests.exceptions.ReadTimeout("timed out"),
    ) as post:
        with pytest.raises(LLMTimeoutError):
            _client().generate("prompt")

    assert post.call_count == 1


def test_generate_raises_llm_unavailable_error_on_http_error_status():
    response = MagicMock()
    response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")

    with patch("ai.llm.ollama_client.requests.post", return_value=response) as post:
        with pytest.raises(LLMUnavailableError):
            _client().generate("prompt")

    assert post.call_count == 1


# ---- reasoning ("thinking") mode ----

@pytest.mark.parametrize("think", [False, True])
def test_generate_sends_configured_think_option(monkeypatch, think):
    monkeypatch.setattr("ai.llm.ollama_client.settings.llm.think", think)
    with patch("ai.llm.ollama_client.requests.post", return_value=_ok_response()) as post:
        _client().generate("prompt")

    assert post.call_args.kwargs["json"]["think"] is think


def test_generate_omits_think_option_when_unset(monkeypatch):
    monkeypatch.setattr("ai.llm.ollama_client.settings.llm.think", None)
    with patch("ai.llm.ollama_client.requests.post", return_value=_ok_response()) as post:
        _client().generate("prompt")

    assert "think" not in post.call_args.kwargs["json"]


def test_think_defaults_off_and_empty_env_means_unset(monkeypatch):
    from app.config.settings import LLMSettings

    monkeypatch.delenv("OLLAMA_THINK", raising=False)
    assert LLMSettings().think is False

    monkeypatch.setenv("OLLAMA_THINK", "")
    assert LLMSettings().think is None
