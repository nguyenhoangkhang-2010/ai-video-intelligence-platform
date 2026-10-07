"""
Summarization previously had zero dedicated tests anywhere in this
project, despite being one of the 8 mandatory pipeline stages - this
file and tests/workers/test_summary_worker.py close that gap.

Tests externally meaningful behavior (what a caller actually observes:
the returned text, what gets raised and when, how much of a long
transcript is actually sent) rather than internal implementation
details like the exact prompt wording.
"""
from unittest.mock import MagicMock

import pytest

from ai.llm.errors import (
    LLMConnectionError,
    LLMEmptyResponseError,
    LLMMalformedResponseError,
    LLMTimeoutError,
)
from ai.summarization.summarizer import Summarizer


def _summarizer(generated_text="a real summary"):
    llm_client = MagicMock(name="llm_client")
    llm_client.generate.return_value = generated_text
    llm_client.model = "qwen3:8b"
    return Summarizer(llm_client=llm_client), llm_client


def test_summarize_returns_the_llm_providers_output_unchanged():
    summarizer, llm_client = _summarizer("Tóm tắt: video nói về lòng can đảm.")

    result = summarizer.summarize("một transcript dài về lòng can đảm")

    assert result == "Tóm tắt: video nói về lòng can đảm."
    llm_client.generate.assert_called_once()


def test_summarize_includes_the_real_transcript_text_in_the_prompt():
    summarizer, llm_client = _summarizer()

    summarizer.summarize("một câu chuyện có thật về việc vượt qua nỗi sợ")

    prompt = llm_client.generate.call_args[0][0]
    assert "một câu chuyện có thật về việc vượt qua nỗi sợ" in prompt


@pytest.mark.parametrize("empty_text", ["", "   ", "\n\t"])
def test_summarize_raises_on_empty_or_whitespace_only_transcript(empty_text):
    summarizer, llm_client = _summarizer()

    with pytest.raises(ValueError):
        summarizer.summarize(empty_text)

    llm_client.generate.assert_not_called()


def test_summarize_truncates_a_transcript_longer_than_max_context_chars():
    summarizer, llm_client = _summarizer()
    long_transcript = "x" * 20_000  # exceeds SummarySettings.max_context_chars (12000)

    summarizer.summarize(long_transcript)

    prompt = llm_client.generate.call_args[0][0]
    # The prompt template adds its own instruction text around the
    # transcript, so assert on the real constraint (no more than
    # max_context_chars of the SOURCE text made it in) rather than the
    # prompt's total length.
    assert "x" * 12_001 not in prompt
    assert "x" * 12_000 in prompt


@pytest.mark.parametrize(
    "llm_error",
    [
        LLMConnectionError("Could not reach Ollama after retrying."),
        LLMTimeoutError("Ollama did not respond in time."),
        LLMEmptyResponseError("Ollama returned no usable text."),
        LLMMalformedResponseError("Ollama response body was not valid JSON."),
    ],
)
def test_summarize_propagates_every_llm_failure_mode_unchanged(llm_error):
    """
    Summarizer has no try/except of its own around the LLM call - a
    real LLM failure must surface as the SAME typed LLMError subtype
    the provider raised, not be swallowed into a fake/empty summary
    and not be wrapped into a different exception type. This is what
    lets app.core.retry.is_transient_error classify it correctly one
    layer up.
    """
    llm_client = MagicMock(name="llm_client")
    llm_client.generate.side_effect = llm_error
    summarizer = Summarizer(llm_client=llm_client)

    with pytest.raises(type(llm_error)) as exc_info:
        summarizer.summarize("a real transcript with real content")

    assert exc_info.value is llm_error
