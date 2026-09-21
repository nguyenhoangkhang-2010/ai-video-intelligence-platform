from unittest.mock import MagicMock, call, patch

import pytest

from app.pipelines.upload_pipeline import UploadPipeline


def test_upload_pipeline_creates_job_then_dispatches_canonical_task():
    processing_job_service = MagicMock(name="processing_job_service")

    job = MagicMock(name="job")
    job.id = 42
    processing_job_service.create_processing_job.return_value = job

    pipeline = UploadPipeline(
        processing_job_service=processing_job_service,
    )

    with patch("app.pipelines.upload_pipeline.process_video") as mock_process_video:
        manager = MagicMock()
        manager.attach_mock(
            processing_job_service.create_processing_job,
            "create_processing_job",
        )
        manager.attach_mock(mock_process_video.delay, "delay")

        result = pipeline.process(
            video_id=10,
            video_path="/tmp/video.mp4",
        )

        # Job creation, exactly once, with the expected arguments.
        processing_job_service.create_processing_job.assert_called_once_with(
            video_id=10,
            job_type="transcription",
        )

        # Celery dispatch, exactly once, with the created job's id,
        # video_id, and video_path - never the Celery broker itself.
        mock_process_video.delay.assert_called_once_with(
            42,
            10,
            "/tmp/video.mp4",
        )

        # The returned object is the exact same job created above.
        assert result is job

        # Job creation must happen before dispatch.
        assert manager.mock_calls == [
            call.create_processing_job(
                video_id=10,
                job_type="transcription",
            ),
            call.delay(42, 10, "/tmp/video.mp4"),
        ]


def test_upload_pipeline_does_not_dispatch_when_job_creation_fails():
    processing_job_service = MagicMock(name="processing_job_service")
    processing_job_service.create_processing_job.side_effect = RuntimeError(
        "database unavailable",
    )

    pipeline = UploadPipeline(
        processing_job_service=processing_job_service,
    )

    with patch("app.pipelines.upload_pipeline.process_video") as mock_process_video:
        with pytest.raises(RuntimeError, match="database unavailable"):
            pipeline.process(
                video_id=10,
                video_path="/tmp/video.mp4",
            )

        mock_process_video.delay.assert_not_called()
