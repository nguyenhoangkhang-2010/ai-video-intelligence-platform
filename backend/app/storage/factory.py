"""Selects a StorageBackend implementation based on settings.storage.backend."""
from app.config.settings import settings
from app.storage.base import StorageBackend
from app.storage.local import LocalFilesystemStorage


def get_storage_backend() -> StorageBackend:
    """
    Returns the configured StorageBackend. Defaults to
    LocalFilesystemStorage (STORAGE_BACKEND=local) - existing
    behavior is unchanged unless an operator explicitly opts into
    STORAGE_BACKEND=s3.
    """
    if settings.storage.backend == "s3":
        from app.storage.s3 import S3StorageBackend

        return S3StorageBackend()

    return LocalFilesystemStorage()
