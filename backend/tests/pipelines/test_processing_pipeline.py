from unittest.mock import MagicMock, call

import pytest

from app.pipelines.processing_pipeline import ProcessingPipeline


def _make_pipeline():
    """
    Build a ProcessingPipeline with its three constructor-injected
    dependencies mocked. No real DB, Celery, or AI workers involved -
    VideoPipelineService itself is a mock, so this only exercises
    ProcessingPipeline's own orchestration logic.
    """
    processing_job_service = MagicMock(name="processing_job_service")
    video_service = MagicMock(name="video_service")
    video_pipeline = MagicMock(name="video_pipeline")

    pipeline = ProcessingPipeline(
        processing_job_service=processing_job_service,
        video_service=video_service,
        video_pipeline=video_pipeline,
    )

    return pipeline, processing_job_service, video_service, video_pipeline


def test_run_happy_path_claims_processes_and_completes():
    pipeline, processing_job_service, video_service, video_pipeline = (
        _make_pipeline()
    )

    processing_job_service.start_if_pending.return_value = MagicMock(
        name="claimed_job",
    )

    manager = MagicMock()
    manager.attach_mock(
        processing_job_service.start_if_pending, "start_if_pending",
    )
    manager.attach_mock(video_service.update_status, "update_status")
    manager.attach_mock(video_pipeline.process, "process")
    manager.attach_mock(processing_job_service.complete_job, "complete_job")

    pipeline.run(job_id=1, video_id=10, file_path="/tmp/video.mp4")

    processing_job_service.start_if_pending.assert_called_once_with(1)

    video_pipeline.process.assert_called_once_with(
        job_id=1,
        video_id=10,
        file_path="/tmp/video.mp4",
    )

    video_service.update_status.assert_called_once_with(
        video_id=10,
        status="processing",
    )

    processing_job_service.complete_job.assert_called_once_with(1)
    processing_job_service.fail_job.assert_not_called()

    # Exact production order: claim -> mark video processing -> run the
    # stage work -> mark the job complete.
    assert manager.mock_calls == [
        call.start_if_pending(1),
        call.update_status(video_id=10, status="processing"),
        call.process(job_id=1, video_id=10, file_path="/tmp/video.mp4"),
        call.complete_job(1),
    ]


def test_run_duplicate_claim_is_a_noop():
    pipeline, processing_job_service, video_service, video_pipeline = (
        _make_pipeline()
    )

    # Real ProcessingJobRepository.claim_for_running() returns None when
    # the job is no longer PENDING (already claimed by another
    # delivery, or terminal) - see Commit 2's repository tests.
    processing_job_service.start_if_pending.return_value = None

    result = pipeline.run(job_id=2, video_id=20, file_path="/tmp/video2.mp4")

    assert result is None

    processing_job_service.start_if_pending.assert_called_once_with(2)
    video_service.update_status.assert_not_called()
    video_pipeline.process.assert_not_called()
    processing_job_service.complete_job.assert_not_called()
    processing_job_service.fail_job.assert_not_called()


def test_run_failure_path_fails_job_marks_video_failed_and_reraises():
    pipeline, processing_job_service, video_service, video_pipeline = (
        _make_pipeline()
    )

    processing_job_service.start_if_pending.return_value = MagicMock(
        name="claimed_job",
    )

    error = RuntimeError("whisper exploded")
    video_pipeline.process.side_effect = error

    manager = MagicMock()
    manager.attach_mock(
        processing_job_service.start_if_pending, "start_if_pending",
    )
    manager.attach_mock(video_service.update_status, "update_status")
    manager.attach_mock(video_pipeline.process, "process")
    manager.attach_mock(processing_job_service.fail_job, "fail_job")

    with pytest.raises(RuntimeError) as exc_info:
        pipeline.run(job_id=3, video_id=30, file_path="/tmp/video3.mp4")

    # The original exception propagates untouched, not swallowed or
    # wrapped in a different exception type.
    assert exc_info.value is error

    processing_job_service.fail_job.assert_called_once_with(
        job_id=3,
        error="whisper exploded",
    )

    assert video_service.update_status.call_args_list == [
        call(video_id=30, status="processing"),
        call(video_id=30, status="failed"),
    ]

    processing_job_service.complete_job.assert_not_called()

    # Exact production order: claim -> mark video processing -> the
    # stage work raises -> fail the job -> mark the video failed ->
    # re-raise (fail_job happens before the video is marked failed).
    assert manager.mock_calls == [
        call.start_if_pending(3),
        call.update_status(video_id=30, status="processing"),
        call.process(job_id=3, video_id=30, file_path="/tmp/video3.mp4"),
        call.fail_job(job_id=3, error="whisper exploded"),
        call.update_status(video_id=30, status="failed"),
    ]
