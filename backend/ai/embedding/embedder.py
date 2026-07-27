import logging
import uuid


logger = logging.getLogger(__name__)


class Embedder:
    """Embedding generator."""

    def embed(
        self,
        text: str,
    ) -> list[dict]:
        logger.info(
            "Generating embeddings.",
        )

        return [
            {
                "chunk_index": 0,
                "chunk_text": text,
                "embedding_model": "stub",
                "vector_id": str(uuid.uuid4()),
            }
        ]