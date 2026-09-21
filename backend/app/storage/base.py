"""
Storage backend interface.

A generic key/bytes abstraction over "where do generated/uploaded
artifacts live" - deliberately small (save/read/exists/delete), so a
local filesystem backend and an S3-compatible backend can implement it
identically. `key` is a backend-agnostic relative path (e.g.
"videos/42/source.mp4", "faiss/video.index") - callers never construct
an OS path or an S3 URL themselves.

Scope note: this interface is a foundation for future use, not a
migration of existing call sites. Uploads, temp files, and the FAISS
index already work correctly today through settings.STORAGE_DIR /
TEMP_DIR (a local filesystem path that Docker Compose already mounts
as a persistent volume - see docker-compose.yml/docker-compose.prod.
yml) - this phase does not rewire those call sites onto this
interface, since doing so is a larger, separately-reviewable change
with no functional requirement forcing it now.
"""
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageBackend(Protocol):
    """
    Structural contract for a storage backend, matching this
    project's existing Protocol-based convention for swappable
    collaborators (ai.retrieval.retriever.Retriever,
    ai.reranking.reranker.Reranker) - no inheritance required.
    """

    def save(self, key: str, data: bytes) -> str:
        """Persist `data` under `key`; returns a backend-specific locator."""
        ...

    def read(self, key: str) -> bytes:
        """Return the bytes stored under `key`; raises if it does not exist."""
        ...

    def exists(self, key: str) -> bool:
        """Return whether `key` currently exists in this backend."""
        ...

    def delete(self, key: str) -> None:
        """Remove `key`; a no-op (not an error) if it does not exist."""
        ...

    def get_local_path(self, key: str) -> Path | None:
        """
        Return a real filesystem path for `key` if this backend has
        one, else None (e.g. an S3-backed store). Callers use this to
        serve a file efficiently (streaming, HTTP Range support) via
        a real path instead of loading it fully into memory.
        """
        ...

    def get_url(self, key: str, expires_in: int = 3600) -> str | None:
        """
        Return a directly-fetchable URL for `key` (e.g. an S3
        presigned URL) valid for `expires_in` seconds, or None if this
        backend has no such URL (e.g. local filesystem - callers
        should serve the file themselves via get_local_path instead).
        """
        ...
