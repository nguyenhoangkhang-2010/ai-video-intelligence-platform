import logging

import numpy as np

from ai.embedding.embedder import Embedder
from ai.embedding.vector_store import VectorStore

from app.repositories.embedding import EmbeddingRepository


logger = logging.getLogger(__name__)


class SemanticSearchService:
    """Semantic search using FAISS."""

    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
    ):
        self.embedder = Embedder()
        self.vector_store = VectorStore(
            dimension=1024,
        )
        
        self.embedding_repository = embedding_repository

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search nearest vectors.
        """

        query_embedding = self.embedder.embed(query)

        if not query_embedding:
            logger.warning("Failed to generate query embedding.")
            return []

        vector = np.asarray(
            [query_embedding[0]["vector"]],
            dtype=np.float32,
        )

        distances, indices = self.vector_store.index.search(
            vector,
            top_k,
        )

        results = []

        for index, distance in zip(
            indices[0],
            distances[0],
        ):

            if index == -1:
                continue

            vector_id = self.vector_store.get_vector_id(
                int(index)
            )

            if vector_id is None:
                logger.warning(
                    "No metadata found for index %s",
                    index,
                )
                continue

            embedding_record = self.embedding_repository.get_by_vector_id(
                vector_id,
            )

            if embedding_record is None:
                logger.warning(
                    "Embedding not found for vector_id %s",
                    vector_id,
                )
                continue

            results.append(
                {
                    "vector_id": vector_id,
                    "video_id": embedding_record.video_id,
                    "chunk_index": embedding_record.chunk_index,
                    "chunk_text": embedding_record.chunk_text,
                    "distance": float(distance),
                }
            )
            
        logger.info(
            "Semantic search completed. Found %s results.",
            len(results),
        )

        return results