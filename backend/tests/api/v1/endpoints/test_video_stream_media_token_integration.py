"""
Integration-level coverage for the real media-token authentication
chain on /videos/{video_id}/stream - deliberately NOT overriding
get_current_user_for_media the way test_video_stream.py and
test_video_media_token.py do.

Why this file exists: every other test for these media endpoints
overrides the auth dependency wholesale (`app.dependency_overrides
[get_current_user_for_media] = lambda: current_user`), which proves
the dependency FUNCTION behaves correctly in isolation but never
proves FastAPI actually resolves the real dependency chain for this
route - the real decode_token() call, the real path-parameter-to-
nested-dependency `video_id` injection, and the real UserRepository
lookup. That gap is exactly how a routing/wiring regression could
slip past a fully-green test suite while still being broken for a
real browser hitting a real server. These tests exercise the real
chain end to end (only get_video_service/get_storage_backend are
mocked - the "what bytes to serve" layer, not auth) against a real
in-memory SQLite User row and a real create_media_token()-issued JWT.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - registers every model on Base.metadata
from app.api.deps import get_storage_backend, get_video_service
from app.auth.jwt import create_access_token, create_media_token
from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.user import User


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(db_engine):
    session_local = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    def override_get_db():
        session = session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    session = session_local()
    session.add(
        User(
            id=7,
            username="owner",
            email="owner@example.com",
            hashed_password="hashed",
            is_active=True,
        ),
    )
    session.add(
        User(
            id=8,
            username="deactivated",
            email="deactivated@example.com",
            hashed_password="hashed",
            is_active=False,
        ),
    )
    session.commit()
    session.close()

    with TestClient(app, follow_redirects=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _video(video_id: int = 10, filename: str = "clip.mp4"):
    return MagicMock(id=video_id, filename=filename)


def _wire_storage(client, video_service=None, storage=None):
    video_service = video_service or MagicMock(name="video_service")
    storage = storage or MagicMock(name="storage")
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_storage_backend] = lambda: storage
    return video_service, storage


def test_real_media_token_authenticates_through_the_full_dependency_chain(client, tmp_path):
    video_service, storage = _wire_storage(client)
    video_service.get_video.return_value = _video(video_id=10)

    real_file = tmp_path / "clip.mp4"
    real_file.write_bytes(b"real mp4 bytes")
    storage.get_url.return_value = None
    storage.get_local_path.return_value = real_file

    token = create_media_token(user_id=7, video_id=10)

    response = client.get(f"/api/v1/videos/10/stream?token={token}")

    assert response.status_code == 200
    assert response.content == b"real mp4 bytes"
    video_service.get_video.assert_called_once_with(video_id=10, user_id=7)


def test_range_request_through_the_real_chain_returns_206_with_correct_content_range(client, tmp_path):
    video_service, storage = _wire_storage(client)
    video_service.get_video.return_value = _video(video_id=10)

    real_file = tmp_path / "clip.mp4"
    real_file.write_bytes(b"0123456789" * 10)  # 100 bytes
    storage.get_url.return_value = None
    storage.get_local_path.return_value = real_file

    token = create_media_token(user_id=7, video_id=10)

    response = client.get(
        f"/api/v1/videos/10/stream?token={token}",
        headers={"Range": "bytes=0-9"},
    )

    assert response.status_code == 206
    assert response.content == b"0123456789"
    assert response.headers["content-range"] == "bytes 0-9/100"
    assert response.headers["accept-ranges"] == "bytes"


def test_real_chain_rejects_an_expired_media_token(client):
    _wire_storage(client)
    from datetime import timedelta

    token = create_media_token(user_id=7, video_id=10, expires_delta=timedelta(seconds=-1))

    response = client.get(f"/api/v1/videos/10/stream?token={token}")

    assert response.status_code == 401


def test_real_chain_rejects_a_token_scoped_to_a_different_video(client):
    video_service, _ = _wire_storage(client)
    token = create_media_token(user_id=7, video_id=999)  # scoped to a different video

    response = client.get(f"/api/v1/videos/10/stream?token={token}")

    assert response.status_code == 403
    video_service.get_video.assert_not_called()


def test_real_chain_rejects_the_main_access_token_used_as_a_media_token(client):
    _wire_storage(client)
    access_token = create_access_token(subject="7")

    response = client.get(f"/api/v1/videos/10/stream?token={access_token}")

    assert response.status_code == 401


def test_real_chain_rejects_a_malformed_token(client):
    _wire_storage(client)

    response = client.get("/api/v1/videos/10/stream?token=not-a-real-jwt")

    assert response.status_code == 401


def test_real_chain_rejects_missing_token_and_missing_header(client):
    _wire_storage(client)

    response = client.get("/api/v1/videos/10/stream")

    assert response.status_code == 401


def test_real_chain_rejects_a_deactivated_users_media_token(client):
    _wire_storage(client)
    token = create_media_token(user_id=8, video_id=10)  # user 8 is is_active=False

    response = client.get(f"/api/v1/videos/10/stream?token={token}")

    assert response.status_code == 403


def test_real_chain_returns_404_for_a_video_the_media_token_owner_does_not_own(client):
    video_service, _ = _wire_storage(client)
    video_service.get_video.side_effect = HTTPException(status_code=404, detail="Video not found")

    token = create_media_token(user_id=7, video_id=10)

    response = client.get(f"/api/v1/videos/10/stream?token={token}")

    assert response.status_code == 404
