import logging

import numpy as np

from ai.embedding.index_builder import IndexBuilder

from ai.embedding.index_metadata import IndexMetadata


logger = logging.getLogger(__name__)


class VectorStore:
    """Manage vectors in FAISS."""

    def __init__(
        self,
        dimension: int = 1024,
    ):
        self.builder = IndexBuilder(
            dimension=dimension,
        )

        self.metadata = IndexMetadata()

        if self.builder.exists():
            self.index = self.builder.load_index()
        else:
            self.index = self.builder.create_index()

    def add(
        self,
        vectors: list[list[float]],
        vector_ids: list[str],
    ) -> None:
        """
        Add vectors to FAISS.
        """

        start_index = self.index.ntotal

        np_vectors = np.asarray(
            vectors,
            dtype=np.float32,
        )

        self.index.add(
            np_vectors,
        )

        for i, vector_id in enumerate(vector_ids):
            self.metadata.add(
                index=start_index + i,
                vector_id=vector_id,
            )

        self.builder.save_index(
            self.index,
        )

        logger.info(
            "Added %s vectors to FAISS.",
            len(vectors),
        )

    def get_vector_id(
        self,
        index: int,
    ) -> str | None:
        """
        Get vector id from FAISS index.
        """

        return self.metadata.get_vector_id(
            index,
        )

    def total_vectors(
        self,
    ) -> int:
        """
        Return total vectors.
        """

        return self.index.ntotal