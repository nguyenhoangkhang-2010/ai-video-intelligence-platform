from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_embedding_service
from app.api.deps import get_storage_backend
from app.api.deps import get_video_service
from app.auth.dependencies import get_current_user
from app.main import app
from app.models.user import User


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _make_user(user_id: int) -> User:
    return User(
        id=user_id,
        username="owner",
        email="owner@example.com",
        hashed_password="hashed",
    )


def _make_video(video_id: int, filename: str):
    video = MagicMock(name="video")
    video.id = video_id
    video.filename = filename
    return video


def _make_embedding(vector_id: str):
    embedding = MagicMock(name="embedding")
    embedding.vector_id = vector_id
    return embedding


def test_delete_video_requires_authentication(client):
    response = client.delete("/api/v1/videos/10")

    assert response.status_code == 401


def test_delete_video_not_owned_returns_404_and_never_deletes_anything(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    embedding_service = MagicMock(name="embedding_service")
    storage = MagicMock(name="storage")

    video_service.get_video.side_effect = HTTPException(
        status_code=404, detail="Video not found",
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_embedding_service] = lambda: embedding_service
    app.dependency_overrides[get_storage_backend] = lambda: storage

    response = client.delete("/api/v1/videos/10")

    assert response.status_code == 404
    video_service.delete_video.assert_not_called()
    embedding_service.get_by_video_id.assert_not_called()
    storage.delete.assert_not_called()


def test_delete_video_removes_file_and_faiss_vectors(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    embedding_service = MagicMock(name="embedding_service")
    storage = MagicMock(name="storage")

    video_service.get_video.return_value = _make_video(10, "clip.mp4")
    video_service.delete_video.return_value = {"message": "Video deleted successfully"}
    embedding_service.get_by_video_id.return_value = [
        _make_embedding("v1"),
        _make_embedding("v2"),
    ]

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_embedding_service] = lambda: embedding_service
    app.dependency_overrides[get_storage_backend] = lambda: storage

    with patch("app.api.v1.endpoints.videos.VectorStore") as mock_vector_store_cls:
        response = client.delete("/api/v1/videos/10")

    assert response.status_code == 200
    assert response.json() == {"message": "Video deleted successfully"}

    # Ownership was checked, and via the video fetched before deletion
    # (not after - the DB row is gone by then).
    video_service.get_video.assert_called_once_with(video_id=10, user_id=99)
    video_service.delete_video.assert_called_once_with(video_id=10, user_id=99)

    # The stored file was removed via the same StorageBackend the
    # stream endpoint reads through, keyed exactly like it.
    storage.delete.assert_called_once_with("videos/clip.mp4")

    # This video's vectors were purged from the shared FAISS index via
    # the same replace() mechanism used to swap embeddings on
    # reprocessing - never a full rebuild, never touching other
    # videos' vectors.
    mock_vector_store_cls.return_value.replace.assert_called_once_with(
        remove_vector_ids={"v1", "v2"}, vectors=[], vector_ids=[],
    )


def test_delete_video_still_succeeds_if_storage_cleanup_fails(client):
    """
    Cleanup is best-effort: the DB deletion already succeeded by the
    time storage/FAISS cleanup runs, so a cleanup failure must not
    turn a successful deletion into an error response.
    """
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    embedding_service = MagicMock(name="embedding_service")
    storage = MagicMock(name="storage")

    video_service.get_video.return_value = _make_video(10, "clip.mp4")
    video_service.delete_video.return_value = {"message": "Video deleted successfully"}
    embedding_service.get_by_video_id.return_value = []
    storage.delete.side_effect = OSError("disk error")

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_embedding_service] = lambda: embedding_service
    app.dependency_overrides[get_storage_backend] = lambda: storage

    response = client.delete("/api/v1/videos/10")

    assert response.status_code == 200
    assert response.json() == {"message": "Video deleted successfully"}


def test_delete_video_skips_faiss_cleanup_when_video_has_no_embeddings(client):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    embedding_service = MagicMock(name="embedding_service")
    storage = MagicMock(name="storage")

    video_service.get_video.return_value = _make_video(10, "clip.mp4")
    video_service.delete_video.return_value = {"message": "Video deleted successfully"}
    embedding_service.get_by_video_id.return_value = []

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_embedding_service] = lambda: embedding_service
    app.dependency_overrides[get_storage_backend] = lambda: storage

    with patch("app.api.v1.endpoints.videos.VectorStore") as mock_vector_store_cls:
        response = client.delete("/api/v1/videos/10")

    assert response.status_code == 200
    mock_vector_store_cls.assert_not_called()
