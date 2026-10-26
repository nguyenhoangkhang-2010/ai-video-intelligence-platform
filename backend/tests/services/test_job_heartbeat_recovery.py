"""
Recovery of processing jobs orphaned by a dead worker.

Regression coverage for a real failure mode: when the worker process
died mid-pipeline (container restart, Docker/WSL engine crash, OOM
kill), its job stayed RUNNING forever - the frontend showed
"processing" indefinitely, the Retry button never appeared (retry only
accepts FAILED jobs), and a retry could not re-run the stage the dead
worker had been in, since that stage also stayed RUNNING.

A live worker now refreshes heartbeat_at; a RUNNING job whose
heartbeat has been quiet for longer than
settings.celery.job_heartbeat_timeout_seconds is orphaned and gets
marked FAILED (interrupted), with its RUNNING stage failed too.
These tests run against the real repositories on the in-memory SQLite
schema from conftest.py.
"""
from datetime import UTC, datetime, timedelta

from app.config.settings import settings
from app.models.processing_job import ProcessingJob
from app.models.processing_stage import ProcessingStage
from app.models.user import User
from app.models.video import Video
from app.pipelines.upload_pipeline import UploadPipeline
from app.repositories.processing_job import ProcessingJobRepository
from app.repositories.processing_stage import ProcessingStageRepository
from app.repositories.video import VideoRepository
from app.services.processing_job import ProcessingJobService
from app.services.processing_stage import ProcessingStageService
from app.services.video import VideoService


TIMEOUT = settings.celery.job_heartbeat_timeout_seconds


def _ago(seconds: float) -> datetime:
    return datetime.now(UTC) - timedelta(seconds=seconds)


def _running_job(
    db_session,
    heartbeat_age: float | None,
    started_age: float = 600,
    name: str = "a",
) -> ProcessingJob:
    """A RUNNING job (plus its User/Video parents) with a heartbeat of the given age."""
    user = User(username=f"owner-{name}", email=f"{name}@example.com", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    video = Video(
        owner_id=user.id,
        title="clip",
        filename=f"clip-{name}.mp4",
        language="en",
        duration=60,
        status="processing",
    )
    db_session.add(video)
    db_session.commit()

    job = ProcessingJob(
        video_id=video.id,
        job_type="full_pipeline",
        status="RUNNING",
        progress=70,
        current_step="Transcribing",
        started_at=_ago(started_age),
        heartbeat_at=None if heartbeat_age is None else _ago(heartbeat_age),
    )
    db_session.add(job)
    db_session.commit()
    return job


def _add_stage(db_session, job, name: str, status: str, started_age: float | None = None):
    stage = ProcessingStage(
        processing_job_id=job.id,
        stage_name=name,
        status=status,
        attempt_count=1 if status != "PENDING" else 0,
        started_at=None if started_age is None else _ago(started_age),
    )
    db_session.add(stage)
    db_session.commit()
    return stage


def _service(db_session) -> ProcessingJobService:
    return ProcessingJobService(ProcessingJobRepository(db_session))


# --- heartbeat bookkeeping ---------------------------------------------------


def test_claim_stamps_a_fresh_heartbeat(db_session):
    job = _running_job(db_session, heartbeat_age=None)
    job.status = "PENDING"
    job.started_at = None
    db_session.commit()

    claimed = _service(db_session).start_if_pending(job.id)

    assert claimed is not None
    assert claimed.heartbeat_at is not None
    assert claimed.heartbeat_at.replace(tzinfo=UTC) > _ago(5)


def test_touch_heartbeat_refreshes_only_running_jobs(db_session):
    job = _running_job(db_session, heartbeat_age=120)
    service = _service(db_session)

    assert service.heartbeat(job.id) is True
    db_session.refresh(job)
    assert job.heartbeat_at.replace(tzinfo=UTC) > _ago(5)

    job.status = "COMPLETED"
    db_session.commit()
    assert service.heartbeat(job.id) is False


def test_progress_update_counts_as_a_heartbeat(db_session):
    job = _running_job(db_session, heartbeat_age=120)

    ProcessingJobRepository(db_session).update_progress(job, 80, "Generating Summary")

    db_session.refresh(job)
    assert job.heartbeat_at.replace(tzinfo=UTC) > _ago(5)


# --- detecting orphans -------------------------------------------------------


def test_job_with_a_quiet_heartbeat_is_stale(db_session):
    job = _running_job(db_session, heartbeat_age=TIMEOUT + 30)

    stale = _service(db_session).get_stale_running_jobs()

    assert [j.id for j in stale] == [job.id]


def test_job_with_a_recent_heartbeat_is_not_stale_even_if_started_long_ago(db_session):
    """A long transcription that keeps sending heartbeats is alive, not orphaned."""
    _running_job(
        db_session,
        heartbeat_age=5,
        started_age=settings.celery.task_time_limit * 2,
    )

    assert _service(db_session).get_stale_running_jobs() == []


def test_job_without_any_heartbeat_falls_back_to_task_time_limit(db_session):
    young = _running_job(db_session, heartbeat_age=None, started_age=60, name="young")
    old = _running_job(
        db_session,
        heartbeat_age=None,
        started_age=settings.celery.task_time_limit + 60,
        name="old",
    )

    stale_ids = [j.id for j in _service(db_session).get_stale_running_jobs()]

    assert old.id in stale_ids
    assert young.id not in stale_ids


def test_stale_lookup_can_be_scoped_to_one_video(db_session):
    first = _running_job(db_session, heartbeat_age=TIMEOUT + 30, name="first")
    _running_job(db_session, heartbeat_age=TIMEOUT + 30, name="second")

    stale = _service(db_session).get_stale_running_jobs(video_id=first.video_id)

    assert [j.id for j in stale] == [first.id]


# --- recovering orphans ------------------------------------------------------


def test_reconcile_marks_job_failed_and_fails_its_running_stage(db_session):
    job = _running_job(db_session, heartbeat_age=TIMEOUT + 30)
    done = _add_stage(db_session, job, "metadata", "COMPLETED", started_age=500)
    running = _add_stage(db_session, job, "transcription", "RUNNING", started_age=400)
    pending = _add_stage(db_session, job, "summary", "PENDING")

    recovered = _service(db_session).reconcile_stale_running(job)

    assert recovered is not None
    assert recovered.status == "FAILED"
    assert recovered.finished_at is not None
    assert "interrupted" in recovered.error_message.lower()
    assert "retry" in recovered.error_message.lower()

    for stage in (done, running, pending):
        db_session.refresh(stage)
    assert done.status == "COMPLETED"  # completed work is kept
    assert running.status == "FAILED"  # can be claimed again by a retry
    assert pending.status == "PENDING"


def test_reconcile_never_fails_a_job_that_sent_a_heartbeat_meanwhile(db_session):
    """
    The staleness check is repeated inside the UPDATE: if the worker
    sends a heartbeat between the caller's read and the write, the job
    is alive and must be left untouched.
    """
    job = _running_job(db_session, heartbeat_age=TIMEOUT + 30)
    stale = _service(db_session).get_stale_running_jobs()
    assert [j.id for j in stale] == [job.id]

    ProcessingJobRepository(db_session).touch_heartbeat(job.id)  # worker is alive after all

    assert _service(db_session).reconcile_stale_running(stale[0]) is None
    db_session.refresh(job)
    assert job.status == "RUNNING"


def test_reconcile_skips_a_job_that_already_finished(db_session):
    job = _running_job(db_session, heartbeat_age=TIMEOUT + 30)
    job.status = "COMPLETED"
    db_session.commit()

    assert _service(db_session).reconcile_stale_running(job) is None


def test_upload_pipeline_read_path_recovers_orphan_and_marks_video_failed(db_session):
    """
    The processing-jobs endpoint the frontend polls calls
    reconcile_orphaned_jobs; it must turn an orphaned RUNNING job into
    FAILED and the video into "failed", so the UI shows Retry.
    """
    job = _running_job(db_session, heartbeat_age=TIMEOUT + 30)
    pipeline = UploadPipeline(
        processing_job_service=_service(db_session),
        video_service=VideoService(VideoRepository(db_session)),
    )

    pipeline.reconcile_orphaned_jobs(video_id=job.video_id)

    db_session.refresh(job)
    video = db_session.get(Video, job.video_id)
    assert job.status == "FAILED"
    assert video.status == "failed"


def test_upload_pipeline_read_path_leaves_a_live_job_alone(db_session):
    job = _running_job(db_session, heartbeat_age=5)
    pipeline = UploadPipeline(
        processing_job_service=_service(db_session),
        video_service=VideoService(VideoRepository(db_session)),
    )

    pipeline.reconcile_orphaned_jobs(video_id=job.video_id)

    db_session.refresh(job)
    assert job.status == "RUNNING"
    assert db_session.get(Video, job.video_id).status == "processing"


# --- redelivery and retry resume the interrupted stage -----------------------


def test_redelivered_task_reclaims_a_job_with_a_quiet_heartbeat(db_session):
    """
    Celery redelivers an unacked task after a worker dies; that
    redelivery must be able to take the job over as soon as the
    heartbeat is stale, not only after the whole task_time_limit.
    """
    job = _running_job(db_session, heartbeat_age=TIMEOUT + 30, started_age=600)

    assert _service(db_session).start_if_pending(job.id) is not None


def test_redelivered_task_does_not_steal_a_job_with_a_live_heartbeat(db_session):
    job = _running_job(db_session, heartbeat_age=5, started_age=600)

    assert _service(db_session).start_if_pending(job.id) is None


def test_new_run_releases_a_stage_left_running_by_the_dead_attempt(db_session):
    """
    After a retry/redelivery claims the job, the stage the dead worker
    was in (RUNNING, started before this claim) is failed so it can be
    claimed again immediately - while a stage started after the claim
    (i.e. by the current run) is never touched.
    """
    job = _running_job(db_session, heartbeat_age=TIMEOUT + 30, started_age=600)
    leftover = _add_stage(db_session, job, "transcription", "RUNNING", started_age=500)

    claimed = _service(db_session).start_if_pending(job.id)
    assert claimed is not None

    current = _add_stage(db_session, job, "summary", "RUNNING", started_age=0)

    stage_service = ProcessingStageService(ProcessingStageRepository(db_session))
    released = stage_service.release_interrupted(job.id)

    db_session.refresh(leftover)
    db_session.refresh(current)
    assert released == 1
    assert leftover.status == "FAILED"
    assert current.status == "RUNNING"
    assert stage_service.try_claim(job.id, "transcription") is not None


def test_release_does_nothing_for_a_job_that_was_never_claimed(db_session):
    job = _running_job(db_session, heartbeat_age=None)
    job.status = "PENDING"
    job.started_at = None
    db_session.commit()
    stage = _add_stage(db_session, job, "transcription", "RUNNING", started_age=500)

    released = ProcessingStageService(
        ProcessingStageRepository(db_session)
    ).release_interrupted(job.id)

    db_session.refresh(stage)
    assert released == 0
    assert stage.status == "RUNNING"
