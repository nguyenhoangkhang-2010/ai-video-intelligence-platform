import logging

import numpy as np

from ai.embedding.embedder import Embedder
from ai.embedding.vector_store import VectorStore


logger = logging.getLogger(__name__)


class SemanticSearchService:
    """Semantic search using FAISS."""

    def __init__(
        self,
    ):
        self.embedder = Embedder()
        self.vector_store = VectorStore(
            dimension=1024,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ):
        """
        Search nearest vectors.
        """

        embedding = self.embedder.embed(query)

        vector = np.asarray(
            [embedding[0]["vector"]],
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

            results.append(
                {
                    "index": int(index),
                    "distance": float(distance),
                }
            )
            
        logger.info(
            "Semantic search completed. Found %s results.",
            len(results),
        )

        return results