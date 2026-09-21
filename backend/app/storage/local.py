"""Local filesystem StorageBackend implementation."""
import logging
from pathlib import Path

from app.config.settings import STORAGE_DIR

logger = logging.getLogger(__name__)


class LocalFilesystemStorage:
    """
    Default StorageBackend, rooted at `root` (settings.STORAGE_DIR by
    default - the same directory Docker Compose already mounts as a
    persistent named/bind volume for both the api and worker
    services). `key` is joined onto `root`; parent directories are
    created on save as needed.
    """

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root is not None else STORAGE_DIR

    def _resolve(self, key: str) -> Path:
        path = (self.root / key).resolve()

        if self.root.resolve() not in path.parents and path != self.root.resolve():
            raise ValueError(f"Storage key escapes root: {key!r}")

        return path

    def save(self, key: str, data: bytes) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    def read(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        try:
            path.unlink()
        except FileNotFoundError:
            pass
