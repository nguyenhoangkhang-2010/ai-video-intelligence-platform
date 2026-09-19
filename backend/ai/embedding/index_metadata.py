import json
import os
from pathlib import Path

from app.config.settings import STORAGE_DIR


class IndexMetadata:
    """Manage FAISS index metadata mapping (index position <-> vector_id)."""

    def __init__(self):

        self.path = (
            STORAGE_DIR
            / "faiss"
            / "metadata.json"
        )

        self.mapping: dict[str, str] = {}
        self.reverse: dict[str, int] = {}

        self.reload()


    def reload(self):
        """
        Reload the mapping from disk, discarding in-memory state.
        Used to pick up the latest committed state before a write.
        """
        if self.path.exists():
            self.mapping = json.loads(
                self.path.read_text(
                    encoding="utf-8",
                )
            )
        else:
            self.mapping = {}

        self.reverse = {
            vector_id: int(index)
            for index, vector_id in self.mapping.items()
        }


    def add(
        self,
        index: int,
        vector_id: str,
    ):
        """
        Record a mapping in memory. Call `save()` once after a batch
        of adds instead of persisting on every single call.
        """
        self.mapping[str(index)] = vector_id
        self.reverse[vector_id] = index


    def exists(
        self,
        vector_id: str,
    ) -> bool:
        return vector_id in self.reverse


    def get_vector_id(
        self,
        index: int,
    ) -> str | None:

        return self.mapping.get(
            str(index)
        )


    def get_index(
        self,
        vector_id: str,
    ) -> int | None:

        return self.reverse.get(
            vector_id
        )


    def save(self):
        """
        Persist the mapping atomically (write to a temp file, then
        rename over the target) so readers never see a half-written
        metadata file.
        """
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        tmp_path = self.path.with_name(
            self.path.name + ".tmp",
        )

        tmp_path.write_text(
            json.dumps(
                self.mapping,
                indent=2,
            ),
            encoding="utf-8",
        )

        os.replace(
            tmp_path,
            self.path,
        )