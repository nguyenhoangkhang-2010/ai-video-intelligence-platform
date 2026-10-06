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