from unittest.mock import MagicMock

import pytest

from app.pipelines.meeting_pipeline import MeetingPipeline


def test_meeting_pipeline_delegates_to_processing_pipeline():
    processing_pipeline = MagicMock(name="processing_pipeline")

    pipeline = MeetingPipeline(
        processing_pipeline=processing_pipeline,
    )

    pipeline.run(
        job_id=42,
        video_id=10,
        file_path="/tmp/video.mp4",
    )

    processing_pipeline.run.assert_called_once_with(
        job_id=42,
        video_id=10,
        file_path="/tmp/video.mp4",
    )


def test_meeting_pipeline_propagates_exception_from_processing_pipeline():
    processing_pipeline = MagicMock(name="processing_pipeline")
    error = RuntimeError("processing failed")
    processing_pipeline.run.side_effect = error

    pipeline = MeetingPipeline(
        processing_pipeline=processing_pipeline,
    )

    with pytest.raises(RuntimeError) as exc_info:
        pipeline.run(
            job_id=42,
            video_id=10,
            file_path="/tmp/video.mp4",
        )

    # The original exception propagates untouched, not swallowed or
    # wrapped in a different exception type.
    assert exc_info.value is error

    processing_pipeline.run.assert_called_once_with(
        job_id=42,
        video_id=10,
        file_path="/tmp/video.mp4",
    )
