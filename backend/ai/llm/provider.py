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
