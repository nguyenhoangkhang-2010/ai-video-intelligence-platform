import logging
import os
from pathlib import Path

import faiss

from app.config.settings import STORAGE_DIR


logger = logging.getLogger(__name__)


class IndexBuilder:
    """Build and manage FAISS vector index."""

    def __init__(
        self,
        dimension: int,
        index_path: str | Path | None = None,
    ):
        self.dimension = dimension
        self.index_path = (
            Path(index_path)
            if index_path is not None
            else STORAGE_DIR / "faiss" / "video.index"
        )

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
        Save FAISS index to disk atomically (write to a temp file,
        then rename over the target so a crash mid-write can never
        leave a corrupt/partial index on disk).
        """
        logger.info(
            "Saving FAISS index.",
        )

        tmp_path = self.index_path.with_name(
            self.index_path.name + ".tmp",
        )

        faiss.write_index(
            index,
            str(tmp_path),
        )

        os.replace(
            tmp_path,
            self.index_path,
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