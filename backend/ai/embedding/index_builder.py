import logging
from pathlib import Path

import faiss


logger = logging.getLogger(__name__)


class IndexBuilder:
    """Build and manage FAISS vector index."""

    def __init__(
        self,
        dimension: int,
        index_path: str = "storage/faiss/video.index",
    ):
        self.dimension = dimension
        self.index_path = Path(index_path)

        self.index_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def create_index(
        self,
    ) -> faiss.IndexFlatL2:
        """
        Create an empty FAISS index.
        """
        logger.info(
            "Creating FAISS index.",
        )

        return faiss.IndexFlatL2(
            self.dimension,
        )

    def save_index(
        self,
        index: faiss.Index,
    ) -> None:
        """
        Save FAISS index to disk.
        """
        logger.info(
            "Saving FAISS index.",
        )

        faiss.write_index(
            index,
            str(self.index_path),
        )

    def load_index(
        self,
    ) -> faiss.Index:
        """
        Load FAISS index.
        """
        logger.info(
            "Loading FAISS index.",
        )

        return faiss.read_index(
            str(self.index_path),
        )

    def exists(
        self,
    ) -> bool:
        """
        Check whether index exists.
        """
        return self.index_path.exists()