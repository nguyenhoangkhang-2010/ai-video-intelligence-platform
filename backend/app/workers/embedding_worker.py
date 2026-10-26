import logging

from ai.embedding.factory import get_embedding_provider
from ai.embedding.provider import EmbeddingProvider


logger = logging.getLogger(__name__)


class EmbeddingWorker:
    """Worker for embedding generation."""

    def __init__(
        self,
        embedder: EmbeddingProvider | None = None,
    ):
        self.embedder = embedder or get_embedding_provider()

    def process(
        self,
        transcript: str,
        video_id: int | str | None = None,
    ) -> list[dict]:
        """
        Generate embeddings from transcript.
        """
        logger.info(
            "Start embedding worker.",
        )

        embeddings = self.embedder.embed(
            transcript,
            video_id=video_id,
        )

        logger.info(
            "Embedding generation completed.",
        )

        return embeddings

    def process_texts(
        self,
        texts: list[str],
        video_id: int | str | None = None,
        start_index: int = 0,
    ) -> list[dict]:
        """Embed separate passages (visual segments) one chunk each."""
        return self.embedder.embed_texts(
            texts,
            video_id=video_id,
            start_index=start_index,
        )

    def similarity(
        self,
        a: str,
        b: str,
    ) -> float | None:
        """Cosine similarity of two texts' query embeddings; None if either is blank."""
        from ai.vision.segments import cosine

        if not a.strip() or not b.strip():
            return None
        return cosine(self.embedder.embed_query(a), self.embedder.embed_query(b))