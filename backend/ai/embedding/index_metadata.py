import json
from pathlib import Path

from app.config.settings import STORAGE_DIR


class IndexMetadata:
    """Manage FAISS index metadata mapping."""

    def __init__(self):
        
        self.path = (
            STORAGE_DIR
            / "faiss"
            / "metadata.json"
        )

        if self.path.exists():
            self.mapping = json.loads(
                self.path.read_text(
                    encoding="utf-8",
                )
            )
        else:
            self.mapping = {}


    def add(
        self,
        index: int,
        vector_id: str,
    ):
        self.mapping[str(index)] = vector_id
        self.save()


    def get_vector_id(
        self,
        index: int,
    ) -> str | None:

        return self.mapping.get(
            str(index)
        )


    def save(self):
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.path.write_text(
            json.dumps(
                self.mapping,
                indent=2,
            ),
            encoding="utf-8",
        )