from collections.abc import Iterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """
    Structural contract for anything that can generate text from a
    prompt.

    Mirrors ai.retrieval.retriever.Retriever and
    ai.reranking.reranker.Reranker's Protocol-based design: no
    inheritance required, so OllamaClient or any future provider
    (a different local model, an OpenAI-compatible endpoint, etc.)
    only needs to match this shape. Every call site that currently
    type-hints `OllamaClient` directly (ChapterLabeler, Summarizer,
    Translator, QuizGenerator and its three sub-generators,
    FlashcardGenerator, RagAnswerer) can depend on this instead
    without any change to its own logic - OllamaClient already
    satisfies this shape exactly as it is today.
    """

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate text for `prompt`. Implementations raise one of
        ai.llm.errors.LLMError's subtypes on failure (connection,
        timeout, unavailable, empty/malformed response) rather than a
        provider-specific exception, so callers can handle failure
        uniformly regardless of which provider is configured.
        """
        ...


@runtime_checkable
class StreamingLLMProvider(LLMProvider, Protocol):
    """
    An LLMProvider that can also yield its output incrementally.

    Optional: callers that want streaming (RagAnswerer.answer_stream)
    check for this shape and fall back to a single `generate` call
    for providers that don't implement it, so adding streaming never
    forces every provider to support it.
    """

    def generate_stream(
        self,
        prompt: str,
    ) -> Iterator[str]:
        """
        Yield the generated text piece by piece. Raises the same
        ai.llm.errors.LLMError subtypes as `generate`, before the
        first piece or mid-stream.
        """
        ...
