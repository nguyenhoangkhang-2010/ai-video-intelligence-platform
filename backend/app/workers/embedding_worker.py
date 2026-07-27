import logging

from ai.embedding.embedder import Embedder


logger = logging.getLogger(__name__)


class EmbeddingWorker:
    """Worker for embedding generation."""

    def __init__(
        self,
    ):
        self.embedder = Embedder()

    def process(
        self,
        transcript: str,
    ) -> list[dict]:
        """
        Generate embeddings from transcript.
        """
        logger.info(
            "Start embedding worker.",
        )

        embeddings = self.embedder.embed(
            transcript,
        )

        logger.info(
            "Embedding generation completed.",
        )

        return embeddings