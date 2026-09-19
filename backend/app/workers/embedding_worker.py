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