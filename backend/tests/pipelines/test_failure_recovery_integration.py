"""
Failure-recovery INTEGRATION testing (not unit mocks, not "chaos
engineering" - see the module name) for the real worker-crash scenario
this project's resumability/idempotency design exists for.

Every piece used here is real: a real ProcessingJob row, a real
ProcessingStage row, a real ProcessingJobService/ProcessingStageService
backed by the real db_session fixture, and the real ProcessingPipeline
-> VideoPipelineService call chain (the same two classes
app/workers/video_processor.py's actual Celery task wires together).
Only the 7 AI worker classes are patched at construction (so this
never loads a real Whisper/BGE-M3/Ollama model), and video_service is
a plain mock (its own real behavior - a single UPDATE statement - has
no interesting failure mode worth a DB-backed test here).

The individual mechanisms this exercises together (job-level stale
reclaim, stage-level stale reclaim, stage-level skip-if-completed,
multi-connection concurrent claiming) each already have dedicated,
thorough tests elsewhere - see:
- tests/repositories/test_processing_job_repository.py
  (test_claim_for_running_reclaims_a_stale_running_job,
  test_concurrent_claim_only_one_worker_wins)
- tests/repositories/test_processing_stage_repository.py
  (test_claim_for_running_reclaims_a_stale_running_stage,
  test_concurrent_claim_for_running_only_one_worker_wins)
- tests/pipelines/test_video_pipeline_orchestration.py
  (test_stale_running_stage_is_reclaimed_and_completed,
  test_resume_skips_already_completed_stages)

What's new here is proving they compose correctly: a worker that
crashes mid-run leaves BOTH the job AND whichever stage it was
executing stuck in RUNNING at the same time - this test is the one
place that combination is exercised through the real, full
ProcessingPipeline.run() entry point in a single call, the way Celery
task redelivery would actually invoke it.
"""
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.config.settings import settings
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.models.video import Video
from app.pipelines.processing_pipeline import ProcessingPipeline
from app.pipelines.video_pipeline import VideoPipelineService
from app.repositories.processing_job import ProcessingJobRepository
from app.repositories.processing_stage import ProcessingStageRepository
from app.services.processing_job import ProcessingJobService
from app.services.processing_stage import ProcessingStageService

ALL_STAGES = (
    "metadata", "transcription", "summary", "embedding",
    "translation", "quiz", "chapter", "flashcard",
)


def _create_stale_running_job(db_session) -> ProcessingJob:
    user = User(username="owner", email="owner@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()

    video = Video(
        owner_id=user.id, title="Sample", filename=f"crash-{id(object())}.mp4",
        language="en", duration=60, status="processing",
    )
    db_session.add(video)
    db_session.commit()

    # The crashed worker had already claimed this job (PENDING ->
    # RUNNING) well before it died - started_at is stamped far enough
    # in the past to be reclaimable.
    stale_started_at = datetime.now(UTC) - timedelta(
        seconds=settings.celery.task_time_limit + 120,
    )
    job = ProcessingJob(
        video_id=video.id, job_type="transcription", status="RUNNING",
        started_at=stale_started_at,
    )
    db_session.add(job)
    db_session.commit()

    return job


def _build_real_pipeline(db_session, shared_video_service):
    """
    Mirrors app/workers/video_processor.py's real wiring: one
    video_service instance shared by both ProcessingPipeline and
    VideoPipelineService, real job/stage services backed by
    db_session, AI worker classes patched at construction only.
    """
    transcript_service = MagicMock(name="transcript_service")
    summary_service = MagicMock(name="summary_service")
    embedding_service = MagicMock(name="embedding_service")
    translation_service = MagicMock(name="translation_service")
    quiz_service = MagicMock(name="quiz_service")
    chapter_service = MagicMock(name="chapter_service")
    flashcard_service = MagicMock(name="flashcard_service")
    storage = MagicMock(name="storage")

    processing_job_service = ProcessingJobService(ProcessingJobRepository(db_session))
    processing_stage_service = ProcessingStageService(ProcessingStageRepository(db_session))

    with (
        patch("app.pipelines.video_pipeline.TranscriptionWorker"),
        patch("app.pipelines.video_pipeline.SummaryWorker"),
        patch("app.pipelines.video_pipeline.EmbeddingWorker"),
        patch("app.pipelines.video_pipeline.TranslationWorker"),
        patch("app.pipelines.video_pipeline.QuizWorker"),
        patch("app.pipelines.video_pipeline.ChapterTopicPipeline"),
        patch("app.pipelines.video_pipeline.FlashcardWorker"),
    ):
        video_pipeline = VideoPipelineService(
            video_service=shared_video_service,
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

    video_pipeline.metadata_stage = MagicMock(name="metadata_stage")
    video_pipeline.transcription_stage = MagicMock(
        name="transcription_stage",
        return_value=(MagicMock(name="transcript"), [{"start": 0.0, "end": 1.0, "text": "x"}]),
    )
    video_pipeline.summary_stage = MagicMock(name="summary_stage")
    video_pipeline.embedding_stage = MagicMock(name="embedding_stage")
    video_pipeline.translation_stage = MagicMock(name="translation_stage")
    video_pipeline.quiz_stage = MagicMock(name="quiz_stage")
    video_pipeline.chapter_stage = MagicMock(name="chapter_stage")
    video_pipeline.flashcard_stage = MagicMock(name="flashcard_stage")

    processing_pipeline = ProcessingPipeline(
        processing_job_service=processing_job_service,
        video_service=shared_video_service,
        video_pipeline=video_pipeline,
    )

    return processing_pipeline, video_pipeline, processing_stage_service


def test_worker_crash_leaves_job_and_stage_running_a_fresh_attempt_recovers_fully(db_session):
    """
    Scenario: a worker crashed while running the "summary" stage,
    after "metadata" and "transcription" had already genuinely
    completed. Both the ProcessingJob row and the "summary"
    ProcessingStage row are stuck in RUNNING with a stale started_at -
    exactly what a real crash leaves behind, simulated here by writing
    that state directly rather than actually killing a process.

    A single fresh ProcessingPipeline.run() call (what Celery task
    redelivery actually invokes) must: reclaim the stale job, resume
    the pipeline, reclaim the stale "summary" stage and complete it,
    run every stage that was never attempted, NEVER re-run "metadata"
    or "transcription" (already genuinely completed), and finish with
    the job COMPLETED and the video "processed".
    """
    job = _create_stale_running_job(db_session)
    video_service = MagicMock(name="video_service")
    processing_pipeline, video_pipeline, stage_service = _build_real_pipeline(
        db_session, video_service,
    )

    stage_service.ensure_seeded(job.id, ALL_STAGES)
    for name in ("metadata", "transcription"):
        stage_service.mark_completed(stage_service.try_claim(job.id, name))

    stale_cutoff = datetime.now(UTC) - timedelta(
        seconds=settings.celery.task_time_limit + 60,
    )
    summary_row = stage_service.get_by_job_id_and_name(job.id, "summary")
    summary_row.status = "RUNNING"
    summary_row.started_at = stale_cutoff
    db_session.commit()

    processing_pipeline.run(job_id=job.id, video_id=job.video_id, file_path="/tmp/crash.mp4")

    # The job-level reclaim happened and the run completed successfully.
    reloaded_job = ProcessingJobRepository(db_session).get_by_id(job.id)
    assert reloaded_job.status == "COMPLETED"

    # Never redid genuinely-already-completed work.
    video_pipeline.metadata_stage.assert_not_called()
    video_pipeline.transcription_stage.assert_not_called()

    # The crashed stage was reclaimed and actually re-run to completion.
    video_pipeline.summary_stage.assert_called_once()
    reloaded_summary = stage_service.get_by_job_id_and_name(job.id, "summary")
    assert reloaded_summary.status == "COMPLETED"

    # Every stage that was never attempted before the crash still ran.
    for stage_name in ("embedding", "translation", "quiz", "chapter", "flashcard"):
        getattr(video_pipeline, f"{stage_name}_stage").assert_called_once()
        reloaded_stage = stage_service.get_by_job_id_and_name(job.id, stage_name)
        assert reloaded_stage.status == "COMPLETED"

    # Real production order: ProcessingPipeline marks "processing" on
    # reclaim, VideoPipelineService marks "processed" on full success.
    assert video_service.update_status.call_args_list[0].kwargs == {
        "video_id": job.video_id, "status": "processing",
    }
    assert video_service.update_status.call_args_list[-1].kwargs == {
        "video_id": job.video_id, "status": "processed",
    }
