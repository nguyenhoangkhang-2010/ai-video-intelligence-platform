from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from app.pipelines.processing_pipeline import ProcessingPipeline


def _pipeline_with_recording_heartbeat():
    events: list[str] = []

    @contextmanager
    def heartbeat(job_id):
        events.append(f"heartbeat-start:{job_id}")
        try:
            yield
        finally:
            events.append(f"heartbeat-stop:{job_id}")

    processing_job_service = MagicMock(name="processing_job_service")
    video_service = MagicMock(name="video_service")
    video_pipeline = MagicMock(name="video_pipeline")
    video_pipeline.process.side_effect = lambda **_: events.append("process")

    pipeline = ProcessingPipeline(
        processing_job_service=processing_job_service,
        video_service=video_service,
        video_pipeline=video_pipeline,
        heartbeat=heartbeat,
    )
    return pipeline, processing_job_service, video_pipeline, events


def test_heartbeat_wraps_the_stage_work_after_a_successful_claim():
    pipeline, processing_job_service, _, events = _pipeline_with_recording_heartbeat()
    processing_job_service.start_if_pending.return_value = MagicMock(name="claimed")

    pipeline.run(job_id=7, video_id=3, file_path="/tmp/v.mp4")

    assert events == ["heartbeat-start:7", "process", "heartbeat-stop:7"]


def test_heartbeat_never_starts_when_the_claim_is_lost():
    """
    A duplicate delivery that loses the claim must not refresh the
    heartbeat of a job another worker owns - otherwise a dead worker's
    job could be kept looking alive.
    """
    pipeline, processing_job_service, video_pipeline, events = (
        _pipeline_with_recording_heartbeat()
    )
    processing_job_service.start_if_pending.return_value = None

    pipeline.run(job_id=7, video_id=3, file_path="/tmp/v.mp4")

    assert events == []
    video_pipeline.process.assert_not_called()


def test_heartbeat_stops_when_a_stage_raises():
    pipeline, processing_job_service, video_pipeline, events = (
        _pipeline_with_recording_heartbeat()
    )
    processing_job_service.start_if_pending.return_value = MagicMock(name="claimed")
    video_pipeline.process.side_effect = RuntimeError("stage blew up")

    with pytest.raises(RuntimeError):
        pipeline.run(job_id=7, video_id=3, file_path="/tmp/v.mp4")

    assert events == ["heartbeat-start:7", "heartbeat-stop:7"]
    processing_job_service.fail_job.assert_called_once()
