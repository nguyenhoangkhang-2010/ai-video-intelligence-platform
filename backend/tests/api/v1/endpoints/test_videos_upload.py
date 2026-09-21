from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_upload_pipeline
from app.api.deps import get_video_service
from app.auth.dependencies import get_current_user
from app.main import app
from app.models.user import User
from app.models.video import Video
from app.types.video_metadata import VideoMetadata


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


def _make_video(video_id: int, owner_id: int, filename: str) -> Video:
    now = datetime.now(timezone.utc)
    return Video(
        id=video_id,
        owner_id=owner_id,
        title="clip.mp4",
        filename=filename,
        language="unknown",
        duration=42,
        status="uploaded",
        created_at=now,
        updated_at=now,
    )


def test_upload_video_authenticated_dispatches_via_upload_pipeline(client, tmp_path):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    upload_pipeline = MagicMock(name="upload_pipeline")

    created_video = _make_video(video_id=10, owner_id=99, filename="placeholder.mp4")
    video_service.upload_video.return_value = created_video

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_upload_pipeline] = lambda: upload_pipeline

    fake_metadata = VideoMetadata(
        duration=42, width=1920, height=1080, fps=30.0, codec="h264",
    )

    with (
        patch(
            "app.api.v1.endpoints.videos.extract_metadata",
            return_value=fake_metadata,
        ),
        patch("app.api.v1.endpoints.videos.VIDEO_UPLOAD_DIR", tmp_path),
    ):
        response = client.post(
            "/api/v1/videos/upload",
            files={"file": ("clip.mp4", b"fake-video-bytes", "video/mp4")},
        )

    # Existing response contract: the created video, as VideoRead.
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 10
    assert body["owner_id"] == 99
    assert body["duration"] == 42
    assert body["status"] == "uploaded"

    # VideoService received the extracted metadata and the correct
    # owner/title.
    video_service.upload_video.assert_called_once()
    upload_kwargs = video_service.upload_video.call_args.kwargs
    assert upload_kwargs["owner_id"] == 99
    assert upload_kwargs["title"] == "clip.mp4"
    assert upload_kwargs["language"] == "unknown"
    assert upload_kwargs["duration"] == 42
    generated_filename = upload_kwargs["filename"]
    assert generated_filename.endswith("_clip.mp4")

    # The endpoint uses UploadPipeline (via get_upload_pipeline) to
    # dispatch, with the just-created video's id and the actual
    # on-disk path of the uploaded file.
    upload_pipeline.process.assert_called_once()
    process_kwargs = upload_pipeline.process.call_args.kwargs
    assert process_kwargs["video_id"] == 10
    assert process_kwargs["video_path"].endswith(generated_filename)

    # The file was genuinely written (isolated to tmp_path, not the
    # real project storage/videos/ directory).
    written_files = list(tmp_path.iterdir())
    assert len(written_files) == 1
    assert written_files[0].name == generated_filename
    assert written_files[0].read_bytes() == b"fake-video-bytes"


def test_upload_video_pipeline_dispatch_failure_is_not_swallowed(client, tmp_path):
    current_user = _make_user(user_id=99)
    video_service = MagicMock(name="video_service")
    upload_pipeline = MagicMock(name="upload_pipeline")

    created_video = _make_video(video_id=11, owner_id=99, filename="placeholder2.mp4")
    video_service.upload_video.return_value = created_video
    upload_pipeline.process.side_effect = RuntimeError("dispatch failed")

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_video_service] = lambda: video_service
    app.dependency_overrides[get_upload_pipeline] = lambda: upload_pipeline

    fake_metadata = VideoMetadata(
        duration=10, width=640, height=480, fps=24.0, codec="h264",
    )

    with (
        patch(
            "app.api.v1.endpoints.videos.extract_metadata",
            return_value=fake_metadata,
        ),
        patch("app.api.v1.endpoints.videos.VIDEO_UPLOAD_DIR", tmp_path),
    ):
        with pytest.raises(RuntimeError, match="dispatch failed"):
            client.post(
                "/api/v1/videos/upload",
                files={"file": ("clip2.mp4", b"more-bytes", "video/mp4")},
            )

    # The video row is created (and metadata extracted) before
    # dispatch is attempted - the failure happens exactly at the
    # pipeline dispatch step, not earlier, and is not converted into
    # a fake success.
    video_service.upload_video.assert_called_once()
    upload_pipeline.process.assert_called_once()
