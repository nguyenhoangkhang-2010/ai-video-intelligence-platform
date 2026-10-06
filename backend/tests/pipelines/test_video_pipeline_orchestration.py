from datetime import datetime, timedelta, UTC
from unittest.mock import MagicMock, patch

import pytest

from ai.llm.errors import LLMConnectionError
from app.config.settings import settings
from app.core.retry import is_transient_error
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.models.video import Video
from app.pipelines.video_pipeline import VideoPipelineService
from app.repositories.processing_stage import ProcessingStageRepository
from app.services.processing_stage import ProcessingStageService


def _create_job(db_session) -> ProcessingJob:
    user = User(username="owner", email="owner@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()

    video = Video(
        owner_id=user.id, title="Sample", filename=f"video-{id(object())}.mp4",
        language="en", duration=60, status="processing",
    )
    db_session.add(video)
    db_session.commit()

    job = ProcessingJob(video_id=video.id, job_type="transcription", status="RUNNING")
    db_session.add(job)
    db_session.commit()

    return job


def _make_pipeline(db_session):
    """
    Build a VideoPipelineService with a REAL ProcessingStageService
    (backed by db_session) so the orchestration loop's claim/
    dependency/resume logic is genuinely exercised against real stage
    rows - not a mock standing in for stateful DB behavior - while the
    7 AI worker classes are still patched at construction time (so
    __init__ never loads a real Whisper/BGE-M3/Ollama model) and every
    other service is a plain mock, matching every other pipeline test
    in this suite.
    """
    video_service = MagicMock(name="video_service")
    transcript_service = MagicMock(name="transcript_service")
    summary_service = MagicMock(name="summary_service")
    embedding_service = MagicMock(name="embedding_service")
    translation_service = MagicMock(name="translation_service")
    processing_job_service = MagicMock(name="processing_job_service")
    quiz_service = MagicMock(name="quiz_service")
    chapter_service = MagicMock(name="chapter_service")
    flashcard_service = MagicMock(name="flashcard_service")
    storage = MagicMock(name="storage")

    processing_stage_service = ProcessingStageService(
        ProcessingStageRepository(db_session),
    )

    with (
        patch("app.pipelines.video_pipeline.TranscriptionWorker"),
        patch("app.pipelines.video_pipeline.SummaryWorker"),
        patch("app.pipelines.video_pipeline.EmbeddingWorker"),
        patch("app.pipelines.video_pipeline.TranslationWorker"),
        patch("app.pipelines.video_pipeline.QuizWorker"),
        patch("app.pipelines.video_pipeline.ChapterTopicPipeline"),
        patch("app.pipelines.video_pipeline.FlashcardWorker"),
    ):
        pipeline = VideoPipelineService(
            video_service=video_service,
            transcript_service=transcript_service,
            summary_service=summary_service,
            embedding_service=embedding_service,
            translation_service=translation_service,
            processing_job_service=processing_job_service,
            processing_stage_service=processing_stage_service,
            quiz_service=quiz_service,
            chapter_service=chapter_service,
            flashcard_service=flashcard_service,
            storage=storage,
        )

    # Every test replaces the stage methods it cares about with its
    # own MagicMock - default every stage to a harmless success here
    # so a test only needs to override the ones it's actually testing.
    pipeline.metadata_stage = MagicMock(name="metadata_stage")
    pipeline.transcription_stage = MagicMock(
        name="transcription_stage",
        return_value=(MagicMock(name="transcript"), [{"start": 0.0, "end": 1.0, "text": "x"}]),
    )
    pipeline.summary_stage = MagicMock(name="summary_stage")
    pipeline.embedding_stage = MagicMock(name="embedding_stage")
    pipeline.translation_stage = MagicMock(name="translation_stage")
    pipeline.quiz_stage = MagicMock(name="quiz_stage")
    pipeline.chapter_stage = MagicMock(name="chapter_stage")
    pipeline.flashcard_stage = MagicMock(name="flashcard_stage")

    return pipeline, video_service, processing_job_service, processing_stage_service


def test_process_seeds_and_completes_all_eight_stages_on_first_run(db_session):
    job = _create_job(db_session)
    pipeline, video_service, processing_job_service, stage_service = _make_pipeline(db_session)

    pipeline.process(job_id=job.id, video_id=job.video_id, file_path="/tmp/video.mp4")

    stages = {s.stage_name: s for s in stage_service.get_by_job_id(job.id)}
    assert len(stages) == 8
    assert all(stage.status == "COMPLETED" for stage in stages.values())
    assert all(stage.attempt_count == 1 for stage in stages.values())

    pipeline.metadata_stage.assert_called_once()
    pipeline.transcription_stage.assert_called_once()
    pipeline.summary_stage.assert_called_once()
    pipeline.chapter_stage.assert_called_once()

    video_service.update_status.assert_called_once_with(
        video_id=job.video_id, status="processed",
    )
    processing_job_service.update_progress.assert_called_once_with(
        job_id=job.id, progress=100, current_step="Completed",
    )


def test_resume_skips_already_completed_stages(db_session):
    """
    The core resumability guarantee: a stage already COMPLETED from a
    prior attempt must not be re-executed - its persisted artifact
    (here, the transcript) is reused instead.
    """
    job = _create_job(db_session)
    pipeline, _, _, stage_service = _make_pipeline(db_session)

    persisted_transcript = MagicMock(name="persisted_transcript")
    pipeline.transcript_service.get_by_video_id.return_value = persisted_transcript

    # Simulate a prior run that got through metadata+transcription
    # and then crashed - exactly like the first run above, but without
    # actually running it.
    stage_service.ensure_seeded(job.id, ("metadata", "transcription", "summary",
                                          "embedding", "translation", "quiz",
                                          "chapter", "flashcard"))
    for name in ("metadata", "transcription"):
        claimed = stage_service.try_claim(job.id, name)
        stage_service.mark_completed(claimed)

    pipeline.process(job_id=job.id, video_id=job.video_id, file_path="/tmp/video.mp4")

    # transcription_stage (the expensive one) is never re-executed.
    pipeline.metadata_stage.assert_not_called()
    pipeline.transcription_stage.assert_not_called()

    # Downstream stages still ran, using the re-fetched persisted
    # transcript (not an in-memory value from this run, since
    # transcription_stage never ran this run).
    pipeline.summary_stage.assert_called_once_with(
        job_id=job.id, video_id=job.video_id, transcript=persisted_transcript,
    )

    stages = {s.stage_name: s for s in stage_service.get_by_job_id(job.id)}
    assert stages["transcription"].attempt_count == 1  # untouched this run
    assert stages["summary"].status == "COMPLETED"


def test_sibling_failure_does_not_block_independent_sibling(db_session):
    job = _create_job(db_session)
    pipeline, _, _, stage_service = _make_pipeline(db_session)

    pipeline.quiz_stage.side_effect = ValueError("quiz generation failed")

    with pytest.raises(Exception):
        pipeline.process(job_id=job.id, video_id=job.video_id, file_path="/tmp/video.mp4")

    # chapter/flashcard are independent siblings of quiz (all three
    # depend only on transcription) - they must still have run.
    pipeline.chapter_stage.assert_called_once()
    pipeline.flashcard_stage.assert_called_once()

    stages = {s.stage_name: s for s in stage_service.get_by_job_id(job.id)}
    assert stages["quiz"].status == "FAILED"
    assert stages["chapter"].status == "COMPLETED"
    assert stages["flashcard"].status == "COMPLETED"


def test_failed_transcription_leaves_downstream_stages_pending(db_session):
    """
    Downstream stages whose dependency never succeeded must stay
    PENDING (never attempted) - not FAILED, since they were never
    actually tried.
    """
    job = _create_job(db_session)
    pipeline, _, _, stage_service = _make_pipeline(db_session)

    pipeline.transcription_stage.side_effect = ValueError("No speech detected in audio.")

    with pytest.raises(Exception):
        pipeline.process(job_id=job.id, video_id=job.video_id, file_path="/tmp/video.mp4")

    pipeline.summary_stage.assert_not_called()
    pipeline.chapter_stage.assert_not_called()

    stages = {s.stage_name: s for s in stage_service.get_by_job_id(job.id)}
    assert stages["transcription"].status == "FAILED"
    for name in ("summary", "embedding", "translation", "quiz", "chapter", "flashcard"):
        assert stages[name].status == "PENDING"
        assert stages[name].attempt_count == 0


def test_non_retryable_failure_does_not_raise_a_transient_exception_type(db_session):
    job = _create_job(db_session)
    pipeline, _, _, _ = _make_pipeline(db_session)

    pipeline.quiz_stage.side_effect = ValueError("deterministic validation error")

    with pytest.raises(Exception) as exc_info:
        pipeline.process(job_id=job.id, video_id=job.video_id, file_path="/tmp/video.mp4")

    assert not is_transient_error(exc_info.value)


def test_retryable_failure_reraises_the_original_transient_exception_type(db_session):
    """
    A transient failure must propagate as its ORIGINAL exception type
    (not wrapped), so Celery's autoretry_for still recognizes it and
    redelivers the task - the redelivery then resumes at exactly the
    stages still incomplete, thanks to resumability.
    """
    job = _create_job(db_session)
    pipeline, _, _, _ = _make_pipeline(db_session)

    pipeline.summary_stage.side_effect = LLMConnectionError("Ollama unreachable")

    with pytest.raises(LLMConnectionError):
        pipeline.process(job_id=job.id, video_id=job.video_id, file_path="/tmp/video.mp4")


def test_stage_with_exhausted_retry_budget_is_not_reattempted(db_session):
    job = _create_job(db_session)
    pipeline, _, _, stage_service = _make_pipeline(db_session)

    stage_service.ensure_seeded(job.id, ("metadata", "transcription", "summary",
                                          "embedding", "translation", "quiz",
                                          "chapter", "flashcard"))
    for name in ("metadata", "transcription"):
        stage_service.mark_completed(stage_service.try_claim(job.id, name))

    quiz_stage = stage_service.get_by_job_id_and_name(job.id, "quiz")
    quiz_stage.status = "FAILED"
    quiz_stage.attempt_count = settings.celery.task_max_retries
    db_session.commit()

    with pytest.raises(Exception):
        pipeline.process(job_id=job.id, video_id=job.video_id, file_path="/tmp/video.mp4")

    pipeline.quiz_stage.assert_not_called()

    reloaded = stage_service.get_by_job_id_and_name(job.id, "quiz")
    assert reloaded.status == "FAILED"
    assert reloaded.attempt_count == settings.celery.task_max_retries  # unchanged


def test_stale_running_stage_is_reclaimed_and_completed(db_session):
    """
    Worker-crash recovery: a stage left RUNNING by a crashed worker
    (started well beyond task_time_limit ago) must be reclaimable by
    a fresh attempt, not stuck forever.
    """
    job = _create_job(db_session)
    pipeline, _, _, stage_service = _make_pipeline(db_session)

    stage_service.ensure_seeded(job.id, ("metadata", "transcription", "summary",
                                          "embedding", "translation", "quiz",
                                          "chapter", "flashcard"))
    for name in ("metadata", "transcription"):
        stage_service.mark_completed(stage_service.try_claim(job.id, name))

    summary_stage_row = stage_service.get_by_job_id_and_name(job.id, "summary")
    summary_stage_row.status = "RUNNING"
    summary_stage_row.started_at = datetime.now(UTC) - timedelta(
        seconds=settings.celery.task_time_limit + 60,
    )
    db_session.commit()

    pipeline.process(job_id=job.id, video_id=job.video_id, file_path="/tmp/video.mp4")

    pipeline.summary_stage.assert_called_once()

    reloaded = stage_service.get_by_job_id_and_name(job.id, "summary")
    assert reloaded.status == "COMPLETED"
    # The row was force-set to RUNNING directly (simulating a crash
    # mid-attempt) without going through a real claim, so attempt_count
    # was still at its seeded 0 beforehand - this reclaim's own atomic
    # UPDATE is what increments it, to 1.
    assert reloaded.attempt_count == 1


def test_genuinely_recent_running_stage_is_not_reclaimed(db_session):
    """
    The safety-critical counterpart to the above: a RUNNING stage
    that is NOT yet stale (started recently, well within
    task_time_limit) must never be reclaimed - doing so would risk
    two concurrent executions of the same stage.
    """
    job = _create_job(db_session)
    pipeline, _, _, stage_service = _make_pipeline(db_session)

    stage_service.ensure_seeded(job.id, ("metadata", "transcription", "summary",
                                          "embedding", "translation", "quiz",
                                          "chapter", "flashcard"))
    for name in ("metadata", "transcription"):
        stage_service.mark_completed(stage_service.try_claim(job.id, name))

    summary_stage_row = stage_service.get_by_job_id_and_name(job.id, "summary")
    summary_stage_row.status = "RUNNING"
    summary_stage_row.started_at = datetime.now(UTC) - timedelta(seconds=5)
    db_session.commit()

    with pytest.raises(Exception):
        pipeline.process(job_id=job.id, video_id=job.video_id, file_path="/tmp/video.mp4")

    pipeline.summary_stage.assert_not_called()

    reloaded = stage_service.get_by_job_id_and_name(job.id, "summary")
    assert reloaded.status == "RUNNING"  # untouched
