import threading
from datetime import datetime, timedelta, UTC

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.processing_job import ProcessingJob
from app.models.processing_stage import ProcessingStage
from app.models.user import User
from app.models.video import Video
from app.repositories.processing_stage import ProcessingStageRepository


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


def test_create_if_absent_creates_a_pending_row(db_session):
    job = _create_job(db_session)
    repository = ProcessingStageRepository(db_session)

    stage = repository.create_if_absent(job.id, "transcription")

    assert stage.status == "PENDING"
    assert stage.attempt_count == 0
    assert stage.processing_job_id == job.id
    assert stage.stage_name == "transcription"


def test_create_if_absent_is_idempotent(db_session):
    job = _create_job(db_session)
    repository = ProcessingStageRepository(db_session)

    first = repository.create_if_absent(job.id, "transcription")
    second = repository.create_if_absent(job.id, "transcription")

    assert first.id == second.id
    assert len(repository.get_by_job_id(job.id)) == 1


def test_claim_for_running_claims_pending_stage(db_session):
    job = _create_job(db_session)
    repository = ProcessingStageRepository(db_session)
    repository.create_if_absent(job.id, "summary")

    claimed = repository.claim_for_running(job.id, "summary", stale_after_seconds=3600)

    assert claimed is not None
    assert claimed.status == "RUNNING"
    assert claimed.attempt_count == 1
    assert claimed.started_at is not None


def test_claim_for_running_cannot_claim_a_genuinely_running_stage(db_session):
    job = _create_job(db_session)
    repository = ProcessingStageRepository(db_session)
    stage = repository.create_if_absent(job.id, "summary")
    repository.claim_for_running(job.id, "summary", stale_after_seconds=3600)

    second_claim = repository.claim_for_running(job.id, "summary", stale_after_seconds=3600)

    assert second_claim is None

    reloaded = repository.get_by_job_id_and_name(job.id, "summary")
    assert reloaded.attempt_count == 1  # not incremented by the rejected claim


def test_claim_for_running_reclaims_a_stale_running_stage(db_session):
    job = _create_job(db_session)
    repository = ProcessingStageRepository(db_session)
    stage = repository.create_if_absent(job.id, "summary")

    stage.status = "RUNNING"
    stage.started_at = datetime.now(UTC) - timedelta(seconds=7200)
    db_session.commit()

    claimed = repository.claim_for_running(job.id, "summary", stale_after_seconds=3600)

    assert claimed is not None
    assert claimed.status == "RUNNING"
    assert claimed.attempt_count == 1  # incremented exactly once by this reclaim


def test_claim_for_running_reclaims_a_failed_stage_for_retry(db_session):
    job = _create_job(db_session)
    repository = ProcessingStageRepository(db_session)
    stage = repository.create_if_absent(job.id, "summary")
    stage.status = "FAILED"
    stage.attempt_count = 1
    stage.error_message = "previous failure"
    db_session.commit()

    claimed = repository.claim_for_running(job.id, "summary", stale_after_seconds=3600)

    assert claimed.status == "RUNNING"
    assert claimed.attempt_count == 2
    assert claimed.error_message is None  # cleared on a fresh attempt


def test_claim_for_running_cannot_claim_a_completed_stage(db_session):
    job = _create_job(db_session)
    repository = ProcessingStageRepository(db_session)
    stage = repository.create_if_absent(job.id, "summary")
    repository.mark_completed(stage)

    claimed = repository.claim_for_running(job.id, "summary", stale_after_seconds=3600)

    assert claimed is None


def test_mark_completed_sets_status_and_finished_at(db_session):
    job = _create_job(db_session)
    repository = ProcessingStageRepository(db_session)
    repository.create_if_absent(job.id, "summary")
    claimed = repository.claim_for_running(job.id, "summary", stale_after_seconds=3600)

    repository.mark_completed(claimed)

    reloaded = repository.get_by_job_id_and_name(job.id, "summary")
    assert reloaded.status == "COMPLETED"
    assert reloaded.finished_at is not None


def test_mark_failed_sets_status_and_error_message(db_session):
    job = _create_job(db_session)
    repository = ProcessingStageRepository(db_session)
    repository.create_if_absent(job.id, "quiz")
    claimed = repository.claim_for_running(job.id, "quiz", stale_after_seconds=3600)

    repository.mark_failed(claimed, "boom")

    reloaded = repository.get_by_job_id_and_name(job.id, "quiz")
    assert reloaded.status == "FAILED"
    assert reloaded.error_message == "boom"
    assert reloaded.finished_at is not None


def test_mark_skipped_sets_status(db_session):
    job = _create_job(db_session)
    repository = ProcessingStageRepository(db_session)
    stage = repository.create_if_absent(job.id, "flashcard")

    repository.mark_skipped(stage)

    reloaded = repository.get_by_job_id_and_name(job.id, "flashcard")
    assert reloaded.status == "SKIPPED"


def test_concurrent_claim_for_running_only_one_worker_wins(tmp_path):
    """
    Real multi-connection concurrency test, same file-backed-SQLite-
    per-thread technique as
    test_processing_job_repository.py::test_concurrent_claim_only_one_worker_wins
    (a shared in-memory StaticPool connection produced a flaky
    sqlite3.InterfaceError under genuine concurrent cursor use there -
    this avoids that by giving each thread its own real connection to
    the same on-disk database).
    """
    db_path = tmp_path / "concurrent_stage_claim.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    setup_session = SessionLocal()
    job = _create_job(setup_session)
    ProcessingStageRepository(setup_session).create_if_absent(job.id, "summary")
    job_id = job.id
    setup_session.close()
    engine.dispose()

    results: list[ProcessingStage | None] = [None, None]
    errors: list[Exception] = []

    def _claim(index: int) -> None:
        thread_engine = create_engine(f"sqlite:///{db_path}")
        ThreadSessionLocal = sessionmaker(bind=thread_engine, autoflush=False, autocommit=False)
        session = ThreadSessionLocal()
        try:
            results[index] = ProcessingStageRepository(session).claim_for_running(
                job_id, "summary", stale_after_seconds=3600,
            )
        except Exception as exc:  # pragma: no cover
            errors.append(exc)
        finally:
            session.close()
            thread_engine.dispose()

    thread_a = threading.Thread(target=_claim, args=(0,))
    thread_b = threading.Thread(target=_claim, args=(1,))
    thread_a.start()
    thread_b.start()
    thread_a.join()
    thread_b.join()

    assert errors == []

    winners = [result for result in results if result is not None]
    losers = [result for result in results if result is None]
    assert len(winners) == 1
    assert len(losers) == 1

    verify_engine = create_engine(f"sqlite:///{db_path}")
    verify_session = sessionmaker(bind=verify_engine)()
    final = ProcessingStageRepository(verify_session).get_by_job_id_and_name(job_id, "summary")
    assert final.status == "RUNNING"
    assert final.attempt_count == 1  # only the winner's claim incremented it
    verify_session.close()
    verify_engine.dispose()
