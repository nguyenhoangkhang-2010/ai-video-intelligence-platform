from unittest.mock import MagicMock, call, patch

import pytest

from app.pipelines.upload_pipeline import UploadPipeline


def _pipeline(processing_job_service=None, video_service=None):
    return UploadPipeline(
        processing_job_service=(
            processing_job_service or MagicMock(name="processing_job_service")
        ),
        video_service=video_service or MagicMock(name="video_service"),
    )


def test_upload_pipeline_creates_job_then_dispatches_canonical_task():
    processing_job_service = MagicMock(name="processing_job_service")

    job = MagicMock(name="job")
    job.id = 42
    processing_job_service.create_processing_job.return_value = job

    pipeline = _pipeline(processing_job_service=processing_job_service)

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

    pipeline = _pipeline(processing_job_service=processing_job_service)

    with patch("app.pipelines.upload_pipeline.process_video") as mock_process_video:
        with pytest.raises(RuntimeError, match="database unavailable"):
            pipeline.process(
                video_id=10,
                video_path="/tmp/video.mp4",
            )

        mock_process_video.delay.assert_not_called()


def test_upload_pipeline_marks_job_and_video_failed_when_dispatch_raises():
    """
    Regression test for the dual-write gap that left jobs 5/13
    orphaned PENDING forever: if process_video.delay() itself raises
    (broker unreachable, serialization error, ...), the already-
    committed job row must not be left silently PENDING with nothing
    behind it - it must reach an observable FAILED terminal state,
    and the request itself must not crash (the file is already saved
    and the Video row already exists; only its processing failed to
    start).
    """
    processing_job_service = MagicMock(name="processing_job_service")
    video_service = MagicMock(name="video_service")

    job = MagicMock(name="job")
    job.id = 42
    processing_job_service.create_processing_job.return_value = job

    pipeline = _pipeline(
        processing_job_service=processing_job_service,
        video_service=video_service,
    )

    with patch("app.pipelines.upload_pipeline.process_video") as mock_process_video:
        mock_process_video.delay.side_effect = RuntimeError("broker unreachable")

        result = pipeline.process(
            video_id=10,
            video_path="/tmp/video.mp4",
        )

        # Does not raise - the upload request itself still succeeds.
        assert result is job

        processing_job_service.fail_job.assert_called_once()
        fail_kwargs = processing_job_service.fail_job.call_args.kwargs
        assert fail_kwargs["job_id"] == 42
        assert "could not be started" in fail_kwargs["error"]
        assert "broker unreachable" in fail_kwargs["error"]

        video_service.update_status.assert_called_once_with(
            video_id=10,
            status="failed",
        )


def test_reconcile_orphaned_jobs_dispatches_each_orphaned_job_found():
    processing_job_service = MagicMock(name="processing_job_service")
    video_service = MagicMock(name="video_service")

    job_a = MagicMock(name="job_a", id=1, video_id=99, dispatch_attempts=1)
    job_b = MagicMock(name="job_b", id=2, video_id=99, dispatch_attempts=1)
    processing_job_service.get_orphaned_pending_jobs.return_value = [job_a, job_b]

    video = MagicMock(name="video", filename="abc_source.mp4")
    video_service.get_video_by_id.return_value = video

    pipeline = _pipeline(
        processing_job_service=processing_job_service,
        video_service=video_service,
    )

    pipeline.reconcile_orphaned_jobs(video_id=99)

    processing_job_service.get_orphaned_pending_jobs.assert_called_once_with(
        video_id=99,
    )
    assert processing_job_service.reconcile_orphaned_dispatch.call_count == 2


def test_reconcile_one_fails_job_when_video_no_longer_exists():
    processing_job_service = MagicMock(name="processing_job_service")
    video_service = MagicMock(name="video_service")
    video_service.get_video_by_id.return_value = None

    job = MagicMock(name="job", id=5, video_id=123)

    pipeline = _pipeline(
        processing_job_service=processing_job_service,
        video_service=video_service,
    )

    pipeline._reconcile_one(job)

    processing_job_service.fail_job.assert_called_once()
    fail_kwargs_or_args = processing_job_service.fail_job.call_args
    assert fail_kwargs_or_args.args[0] == 5 or fail_kwargs_or_args.kwargs.get("job_id") == 5
    processing_job_service.reconcile_orphaned_dispatch.assert_not_called()


def test_reconcile_one_dispatches_with_path_reconstructed_from_video_filename():
    processing_job_service = MagicMock(name="processing_job_service")
    video_service = MagicMock(name="video_service")

    video = MagicMock(name="video", filename="uuid123_myvideo.mp4")
    video_service.get_video_by_id.return_value = video

    job = MagicMock(name="job", id=7, video_id=321, dispatch_attempts=1)

    pipeline = _pipeline(
        processing_job_service=processing_job_service,
        video_service=video_service,
    )

    with patch("app.pipelines.upload_pipeline.process_video") as mock_process_video:
        pipeline._reconcile_one(job)

        processing_job_service.reconcile_orphaned_dispatch.assert_called_once()
        call_kwargs = processing_job_service.reconcile_orphaned_dispatch.call_args
        assert call_kwargs.args[0] is job
        dispatch_fn = call_kwargs.kwargs["dispatch"]

        # The dispatch closure, when actually invoked, calls
        # process_video.delay with a path built from the video's own
        # filename - not a path the caller has to supply separately.
        dispatch_fn()
        mock_process_video.delay.assert_called_once()
        dispatch_args = mock_process_video.delay.call_args.args
        assert dispatch_args[0] == 7
        assert dispatch_args[1] == 321
        assert "uuid123_myvideo.mp4" in dispatch_args[2]


def test_retry_job_dispatches_with_path_from_video_filename():
    processing_job_service = MagicMock(name="processing_job_service")
    video_service = MagicMock(name="video_service")

    video = MagicMock(name="video", filename="uuid456_retryme.mp4")
    video_service.get_video_by_id.return_value = video

    job = MagicMock(name="job", id=9, video_id=55)

    pipeline = _pipeline(
        processing_job_service=processing_job_service,
        video_service=video_service,
    )

    with patch("app.pipelines.upload_pipeline.process_video") as mock_process_video:
        result = pipeline.retry_job(job)

        mock_process_video.delay.assert_called_once()
        dispatch_args = mock_process_video.delay.call_args.args
        assert dispatch_args[0] == 9
        assert dispatch_args[1] == 55
        assert "uuid456_retryme.mp4" in dispatch_args[2]
        assert result is job
        processing_job_service.fail_job.assert_not_called()


def test_retry_job_fails_job_when_video_no_longer_exists():
    processing_job_service = MagicMock(name="processing_job_service")
    video_service = MagicMock(name="video_service")
    video_service.get_video_by_id.return_value = None

    job = MagicMock(name="job", id=9, video_id=55)

    pipeline = _pipeline(
        processing_job_service=processing_job_service,
        video_service=video_service,
    )

    with patch("app.pipelines.upload_pipeline.process_video") as mock_process_video:
        pipeline.retry_job(job)

        mock_process_video.delay.assert_not_called()
        processing_job_service.fail_job.assert_called_once()
        assert "no longer exists" in processing_job_service.fail_job.call_args.kwargs["error"]


def test_retry_job_marks_job_and_video_failed_when_dispatch_raises():
    processing_job_service = MagicMock(name="processing_job_service")
    video_service = MagicMock(name="video_service")
    video_service.get_video_by_id.return_value = MagicMock(filename="x.mp4")

    job = MagicMock(name="job", id=9, video_id=55)

    pipeline = _pipeline(
        processing_job_service=processing_job_service,
        video_service=video_service,
    )

    with patch("app.pipelines.upload_pipeline.process_video") as mock_process_video:
        mock_process_video.delay.side_effect = RuntimeError("broker unreachable")

        result = pipeline.retry_job(job)

        assert result is job
        processing_job_service.fail_job.assert_called_once_with(
            job_id=9,
            error="Processing could not be started: broker unreachable",
        )
        video_service.update_status.assert_called_once_with(
            video_id=55, status="failed",
        )
