import logging

import faiss
import numpy as np

from ai.embedding.index_builder import IndexBuilder


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

        if self.builder.exists():
            self.index = self.builder.load_index()
        else:
            self.index = self.builder.create_index()

    def add(
        self,
        vectors: list[list[float]],
    ) -> None:
        """
        Add vectors to FAISS.
        """

        np_vectors = np.asarray(
            vectors,
            dtype=np.float32,
        )

        self.index.add(
            np_vectors,
        )

        self.builder.save_index(
            self.index,
        )

        logger.info(
            "Added %s vectors to FAISS.",
            len(vectors),
        )

    def total_vectors(
        self,
    ) -> int:
        """
        Return total vectors.
        """

        return self.index.ntotal