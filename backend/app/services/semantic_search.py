import logging

import numpy as np

from ai.embedding.embedder import Embedder
from ai.embedding.vector_store import VectorStore
from app.repositories.embedding import EmbeddingRepository


logger = logging.getLogger(__name__)


class SemanticSearchService:
    """Semantic search using FAISS, always scoped to a single video."""

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
        video_id: int,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search transcript chunks belonging to `video_id` using
        semantic similarity. The FAISS index is global, so results
        are filtered down to the vector_ids owned by this video
        before being returned.
        """
        if not query or not query.strip():
            return []

        video_embeddings = (
            self.embedding_repository.get_by_video_id(
                video_id,
            )
        )

        if not video_embeddings:
            logger.info(
                "No embeddings found for video %s.",
                video_id,
            )
            return []

        valid_vector_ids = {
            embedding.vector_id
            for embedding in video_embeddings
        }

        total_vectors = self.vector_store.total_vectors()

        if total_vectors == 0:
            logger.warning(
                "Video %s has embedding records but the FAISS "
                "index is empty.",
                video_id,
            )
            return []

        query_vector = self.embedder.embed_query(
            query,
        )

        if not query_vector:
            logger.warning(
                "Failed to generate query embedding."
            )
            return []

        vector = np.asarray(
            [query_vector],
            dtype=np.float32,
        )

        # Search the whole global index (IndexFlatL2 scans every
        # vector regardless of k) then keep only this video's
        # vector_ids, so results never leak chunks from other videos.
        distances, indices = (
            self.vector_store.index.search(
                vector,
                total_vectors,
            )
        )

        results = []

        for index, distance in zip(
            indices[0],
            distances[0],
        ):
            if index == -1:
                continue

            vector_id = (
                self.vector_store.get_vector_id(
                    int(index),
                )
            )

            if vector_id is None or vector_id not in valid_vector_ids:
                continue

            embedding_record = (
                self.embedding_repository
                .get_by_vector_id(vector_id)
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
                    "video_id": (
                        embedding_record.video_id
                    ),
                    "chunk_index": (
                        embedding_record.chunk_index
                    ),
                    "chunk_text": (
                        embedding_record.chunk_text
                    ),
                    "distance": float(distance),
                }
            )

            if len(results) >= top_k:
                break

        logger.info(
            "Semantic search completed for video %s. "
            "Found %s results.",
            video_id,
            len(results),
        )

        return results