import logging

import numpy as np

from ai.embedding.index_builder import IndexBuilder

from ai.embedding.index_metadata import IndexMetadata

from ai.embedding.faiss_lock import FileLock


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

        self.lock_path = self.builder.index_path.with_name(
            self.builder.index_path.name + ".lock",
        )

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

        The whole read-modify-write cycle (reload latest index +
        metadata, append, persist both) runs inside a file lock so
        concurrent Celery workers can't race each other into a lost
        update or a desynced index/metadata pair. Vector ids already
        present in the index are skipped, which keeps inserts
        idempotent on retry/reprocessing.
        """

        if not vectors:
            return

        with FileLock(self.lock_path):
            self.index = (
                self.builder.load_index()
                if self.builder.exists()
                else self.builder.create_index()
            )
            self.metadata.reload()

            new_vectors = []
            new_vector_ids = []

            for vector, vector_id in zip(vectors, vector_ids):
                if self.metadata.exists(vector_id):
                    continue

                new_vectors.append(vector)
                new_vector_ids.append(vector_id)

            skipped = len(vectors) - len(new_vectors)

            if not new_vectors:
                logger.info(
                    "All %s vectors already indexed, skipping.",
                    len(vectors),
                )
                return

            start_index = self.index.ntotal

            np_vectors = np.asarray(
                new_vectors,
                dtype=np.float32,
            )

            self.index.add(
                np_vectors,
            )

            for i, vector_id in enumerate(new_vector_ids):
                self.metadata.add(
                    index=start_index + i,
                    vector_id=vector_id,
                )

            self.builder.save_index(
                self.index,
            )

            self.metadata.save()

        logger.info(
            "Added %s new vectors to FAISS (%s duplicates skipped).",
            len(new_vector_ids),
            skipped,
        )

    def replace(
        self,
        remove_vector_ids: set[str],
        vectors: list[list[float]],
        vector_ids: list[str],
    ) -> None:
        """
        Rebuild the index: drop every existing vector whose id is in
        `remove_vector_ids`, keep every other existing vector
        untouched, then append the given (vectors, vector_ids).

        FAISS's `remove_ids` compacts the index and shifts every
        subsequent position, which would desync the metadata mapping
        for every other video's vectors. A full rebuild (reconstruct
        everything that should survive, build a fresh index, rebuild
        metadata from scratch to match the new positions) avoids that
        entirely and keeps FAISS/metadata guaranteed consistent.
        """

        with FileLock(self.lock_path):
            self.index = (
                self.builder.load_index()
                if self.builder.exists()
                else self.builder.create_index()
            )
            self.metadata.reload()

            kept_vectors = []
            kept_vector_ids = []
            removed_count = 0

            for position in range(self.index.ntotal):
                vector_id = self.metadata.get_vector_id(position)

                if vector_id is None:
                    continue

                if vector_id in remove_vector_ids:
                    removed_count += 1
                    continue

                kept_vectors.append(
                    self.index.reconstruct(position)
                )
                kept_vector_ids.append(vector_id)

            kept_set = set(kept_vector_ids)
            added_count = 0
            duplicate_count = 0

            for vector, vector_id in zip(vectors, vector_ids):
                if vector_id in kept_set:
                    duplicate_count += 1
                    continue

                kept_vectors.append(
                    np.asarray(vector, dtype=np.float32)
                )
                kept_vector_ids.append(vector_id)
                kept_set.add(vector_id)
                added_count += 1

            new_index = self.builder.create_index()

            if kept_vectors:
                new_index.add(
                    np.asarray(kept_vectors, dtype=np.float32)
                )

            new_mapping: dict[str, str] = {}
            new_reverse: dict[str, int] = {}

            for position, vector_id in enumerate(kept_vector_ids):
                new_mapping[str(position)] = vector_id
                new_reverse[vector_id] = position

            self.metadata.mapping = new_mapping
            self.metadata.reverse = new_reverse

            self.builder.save_index(
                new_index,
            )

            self.metadata.save()

            self.index = new_index

        logger.info(
            "FAISS replace complete: removed=%s, added=%s, "
            "duplicates_skipped=%s, total=%s.",
            removed_count,
            added_count,
            duplicate_count,
            len(kept_vector_ids),
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