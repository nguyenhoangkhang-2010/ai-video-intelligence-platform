from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.meetings import get_meeting
from app.models.processing_job import ProcessingJob
from app.models.quiz import Quiz
from app.models.summary import Summary
from app.models.transcript import Transcript
from app.models.translation import Translation
from app.models.user import User
from app.models.video import Video


def _make_current_user(user_id: int) -> User:
    return User(
        id=user_id,
        username="owner",
        email="owner@example.com",
        hashed_password="hashed",
    )


def _make_video(video_id: int, owner_id: int) -> Video:
    now = datetime.now(timezone.utc)
    return Video(
        id=video_id,
        owner_id=owner_id,
        title="Weekly Sync",
        filename="weekly-sync.mp4",
        language="en",
        duration=600,
        status="processed",
        created_at=now,
        updated_at=now,
    )


def _make_transcript(video_id: int) -> Transcript:
    return Transcript(
        id=1,
        video_id=video_id,
        language="en",
        text="hello world",
        word_count=2,
        created_at=datetime.now(timezone.utc),
    )


def _make_processing_job(video_id: int) -> ProcessingJob:
    return ProcessingJob(
        id=1,
        video_id=video_id,
        job_type="transcription",
        status="COMPLETED",
        progress=100,
        current_step="Completed",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        error_message=None,
    )


def _make_summary(video_id: int) -> Summary:
    return Summary(
        id=1,
        video_id=video_id,
        type="default",
        content="a summary",
        model_name="qwen3:8b",
        created_at=datetime.now(timezone.utc),
    )


def _make_translation(video_id: int) -> Translation:
    return Translation(
        id=1,
        video_id=video_id,
        language="vi",
        subtitle="phu de",
        created_at=datetime.now(timezone.utc),
    )


def _make_quiz(video_id: int) -> Quiz:
    return Quiz(
        id=1,
        video_id=video_id,
        type="mcq",
        question="What is discussed?",
        answer="Roadmap",
        options="[]",
        created_at=datetime.now(timezone.utc),
    )


def _make_services():
    """
    One mock per injected service dependency - matches get_meeting's
    real parameter list. No FastAPI TestClient/dependency_overrides
    needed: the endpoint function is called directly.
    """
    return {
        "video_service": MagicMock(name="video_service"),
        "transcript_service": MagicMock(name="transcript_service"),
        "summary_service": MagicMock(name="summary_service"),
        "translation_service": MagicMock(name="translation_service"),
        "quiz_service": MagicMock(name="quiz_service"),
        "processing_job_service": MagicMock(name="processing_job_service"),
    }


def test_get_meeting_aggregates_all_related_data():
    services = _make_services()

    current_user = _make_current_user(user_id=99)

    video = _make_video(video_id=10, owner_id=99)
    services["video_service"].get_video.return_value = video

    transcript = _make_transcript(video_id=10)
    services["transcript_service"].get_by_video_id.return_value = transcript

    job = _make_processing_job(video_id=10)
    services["processing_job_service"].get_jobs_by_video.return_value = [job]

    summary = _make_summary(video_id=10)
    services["summary_service"].get_by_video_id.return_value = [summary]

    translation = _make_translation(video_id=10)
    services["translation_service"].get_by_video_id.return_value = [translation]

    quiz = _make_quiz(video_id=10)
    services["quiz_service"].get_by_video_id.return_value = [quiz]

    response = get_meeting(
        video_id=10,
        current_user=current_user,
        **services,
    )

    # Ownership lookup: video_id and the CURRENT USER's id, not
    # swapped or defaulted to something else.
    services["video_service"].get_video.assert_called_once_with(
        video_id=10,
        user_id=99,
    )

    services["transcript_service"].get_by_video_id.assert_called_once_with(10)
    services["processing_job_service"].get_jobs_by_video.assert_called_once_with(
        video_id=10,
    )
    services["summary_service"].get_by_video_id.assert_called_once_with(
        video_id=10,
    )
    services["translation_service"].get_by_video_id.assert_called_once_with(
        video_id=10,
    )
    services["quiz_service"].get_by_video_id.assert_called_once_with(
        video_id=10,
    )

    # Real model_validate() conversions ran - assert actual data, not
    # just "not None".
    assert response.video.id == 10
    assert response.video.owner_id == 99
    assert response.video.title == "Weekly Sync"
    assert response.video.status == "processed"

    assert response.transcript is not None
    assert response.transcript.id == 1
    assert response.transcript.video_id == 10
    assert response.transcript.text == "hello world"

    assert len(response.processing_jobs) == 1
    assert response.processing_jobs[0].id == 1
    assert response.processing_jobs[0].status == "COMPLETED"

    assert len(response.summaries) == 1
    assert response.summaries[0].id == 1
    assert response.summaries[0].content == "a summary"

    assert len(response.translations) == 1
    assert response.translations[0].id == 1
    assert response.translations[0].language == "vi"

    assert len(response.quizzes) == 1
    assert response.quizzes[0].id == 1
    assert response.quizzes[0].question == "What is discussed?"


def test_get_meeting_handles_video_with_no_related_data_yet():
    services = _make_services()

    current_user = _make_current_user(user_id=99)

    video = _make_video(video_id=11, owner_id=99)
    services["video_service"].get_video.return_value = video

    services["transcript_service"].get_by_video_id.return_value = None
    services["processing_job_service"].get_jobs_by_video.return_value = []
    services["summary_service"].get_by_video_id.return_value = []
    services["translation_service"].get_by_video_id.return_value = []
    services["quiz_service"].get_by_video_id.return_value = []

    response = get_meeting(
        video_id=11,
        current_user=current_user,
        **services,
    )

    assert response.video is not None
    assert response.video.id == 11
    assert response.processing_jobs == []
    assert response.transcript is None
    assert response.summaries == []
    assert response.translations == []
    assert response.quizzes == []


def test_get_meeting_stops_before_aggregating_when_ownership_check_fails():
    services = _make_services()

    current_user = _make_current_user(user_id=99)

    # The real VideoService.get_video() raises exactly this for both
    # "video doesn't exist" and "video belongs to someone else" -
    # confirmed by inspecting app/services/video.py.
    services["video_service"].get_video.side_effect = HTTPException(
        status_code=404,
        detail="Video not found",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_meeting(
            video_id=10,
            current_user=current_user,
            **services,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Video not found"

    # Ownership check first, then STOP - none of the related-resource
    # services are ever touched.
    services["transcript_service"].get_by_video_id.assert_not_called()
    services["processing_job_service"].get_jobs_by_video.assert_not_called()
    services["summary_service"].get_by_video_id.assert_not_called()
    services["translation_service"].get_by_video_id.assert_not_called()
    services["quiz_service"].get_by_video_id.assert_not_called()
