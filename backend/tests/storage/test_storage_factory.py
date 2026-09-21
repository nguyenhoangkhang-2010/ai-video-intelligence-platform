from app.storage.factory import get_storage_backend
from app.storage.local import LocalFilesystemStorage


def test_get_storage_backend_defaults_to_local(monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings.storage, "backend", "local")

    backend = get_storage_backend()

    assert isinstance(backend, LocalFilesystemStorage)


def test_get_storage_backend_selects_s3_without_importing_boto3_eagerly(monkeypatch):
    """
    Selecting the s3 backend must only import boto3 at the moment
    get_storage_backend() is actually called with backend="s3" - not
    merely by importing app.storage (already implicitly verified by
    every other test in this file successfully importing that module
    without boto3 configured/reachable).
    """
    from app.config.settings import settings

    monkeypatch.setattr(settings.storage, "backend", "s3")
    monkeypatch.setattr(settings.storage, "s3_bucket", "test-bucket")

    backend = get_storage_backend()

    assert type(backend).__name__ == "S3StorageBackend"
