from ai.embedding.provider import EmbeddingProvider


def get_embedding_provider() -> EmbeddingProvider:
    """
    Build the configured EmbeddingProvider.

    The single call site every caller should use instead of
    constructing Embedder() directly. Unlike ai.llm.factory.
    get_llm_provider(), there is no settings-driven branch yet: BGE-M3
    is the only embedding implementation this project has, and
    Embedder's own module-level @lru_cache already ensures the
    underlying model loads once per process regardless of how many
    Embedder()/get_embedding_provider() calls construct a wrapper
    around it (see ai.embedding.embedder._load_embedding_model). If a
    second provider is ever added, branch here the same way
    get_llm_provider() branches on settings.llm.provider - there is
    nothing to configure yet, so nothing is added speculatively.
    """
    from ai.embedding.embedder import Embedder

    return Embedder()
