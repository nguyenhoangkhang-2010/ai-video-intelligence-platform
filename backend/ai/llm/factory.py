from ai.llm.provider import LLMProvider
from app.config.settings import settings


def get_llm_provider() -> LLMProvider:
    """
    Build the LLMProvider selected by settings.llm.provider.

    The single call site every AI module should use instead of
    constructing OllamaClient() directly, so adding a second provider
    later is a new branch here, not a change to every call site.
    Deliberately not cached/memoized: OllamaClient itself is a cheap,
    stateless HTTP client (no model loaded into process memory, unlike
    Embedder/CrossEncoderReranker), so there is no reload cost to avoid
    by sharing one instance.
    """
    if settings.llm.provider == "ollama":
        from ai.llm.ollama_client import OllamaClient

        return OllamaClient()

    raise ValueError(
        f"Unknown LLM provider configured: {settings.llm.provider!r}"
    )
