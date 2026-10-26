from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """
    Structural contract for anything that can turn text into dense
    vector embeddings.

    Mirrors ai.llm.provider.LLMProvider / ai.retrieval.retriever.
    Retriever's Protocol-based design: no inheritance required, so
    Embedder (BGE-M3) or any future embedding model only needs to
    match this shape. Every call site that currently constructs
    Embedder() directly (EmbeddingWorker, SemanticSearchService,
    ChapterDetector, TopicSegmenter) can depend on this instead
    without any change to its own logic.
    """

    def embed(
        self,
        text: str,
        video_id: int | str | None = None,
    ) -> list[dict]:
        """
        Chunk `text` and return one dict per chunk with at least
        `chunk_index`, `chunk_text`, `embedding_model`, `vector`, and
        `vector_id` keys - see ai.embedding.embedder.Embedder.embed
        for the exact shape every current caller relies on.
        """
        ...

    def embed_query(
        self,
        query: str,
    ) -> list[float]:
        """Return a single dense vector for `query` (empty list if `query` is blank)."""
        ...
