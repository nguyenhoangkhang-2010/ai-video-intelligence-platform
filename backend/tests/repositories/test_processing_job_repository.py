import threading
from datetime import datetime, timedelta, UTC

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.models.video import Video
from app.repositories.processing_job import ProcessingJobRepository


def _create_user(db_session, username: str = "owner") -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="hashed",
    )
    db_session.add(user)
    db_session.commit()
    return user


def _create_job_for_owner(
    db_session,
    owner: User,
    status: str = "PENDING",
    filename: str | None = None,
) -> ProcessingJob:
    video = Video(
        owner_id=owner.id,
        title="Sample video",
        filename=filename or f"video-{owner.id}-{status}-{id(object())}.mp4",
        language="en",
        duration=60,
        status="uploaded",
    )
    db_session.add(video)
    db_session.commit()

    job = ProcessingJob(
        video_id=video.id,
        job_type="transcription",
        status=status,
    )
    db_session.add(job)
    db_session.commit()

    return job


def _create_job(db_session, status: str = "PENDING") -> ProcessingJob:
    """
    Create a real ProcessingJob row (with its required User/Video
    parents) directly against the fixture's schema.
    """
    owner = _create_user(db_session)
    return _create_job_for_owner(
        db_session, owner, status=status, filename=f"video-{status}.mp4",
    )


def test_claim_for_running_claims_pending_job(db_session):
    job = _create_job(db_session, status="PENDING")
    repository = ProcessingJobRepository(db_session)

    claimed = repository.claim_for_running(job.id)

    assert claimed is not None
    assert claimed.status == "RUNNING"
    assert claimed.started_at is not None


def test_claim_for_running_cannot_claim_same_job_twice(db_session):
    job = _create_job(db_session, status="PENDING")
    repository = ProcessingJobRepository(db_session)

    first_claim = repository.claim_for_running(job.id)
    second_claim = repository.claim_for_running(job.id)

    assert first_claim is not None
    assert second_claim is None

    reloaded = repository.get_by_id(job.id)
    assert reloaded.status == "RUNNING"


def test_claim_for_running_nonexistent_job_returns_none(db_session):
    repository = ProcessingJobRepository(db_session)

    claimed = repository.claim_for_running(999999)

    assert claimed is None


def test_claim_for_running_does_not_reclaim_terminal_job(db_session):
    job = _create_job(db_session, status="COMPLETED")
    repository = ProcessingJobRepository(db_session)

    claimed = repository.claim_for_running(job.id)

    assert claimed is None

    reloaded = repository.get_by_id(job.id)
    assert reloaded.status == "COMPLETED"


def test_get_by_owner_returns_only_jobs_for_that_owners_videos(db_session):
    owner_a = _create_user(db_session, "alice")
    owner_b = _create_user(db_session, "bob")

    job_a1 = _create_job_for_owner(db_session, owner_a, filename="a1.mp4")
    job_a2 = _create_job_for_owner(db_session, owner_a, filename="a2.mp4")
    _create_job_for_owner(db_session, owner_b, filename="b1.mp4")

    repository = ProcessingJobRepository(db_session)

    jobs = repository.get_by_owner(owner_a.id)

    assert {job.id for job in jobs} == {job_a1.id, job_a2.id}


def test_get_by_owner_returns_empty_list_for_owner_with_no_videos(db_session):
    owner = _create_user(db_session, "lonely")
    repository = ProcessingJobRepository(db_session)

    assert repository.get_by_owner(owner.id) == []


def test_get_by_id_and_owner_returns_job_for_correct_owner(db_session):
    owner = _create_user(db_session, "alice")
    job = _create_job_for_owner(db_session, owner, filename="a1.mp4")
    repository = ProcessingJobRepository(db_session)

    found = repository.get_by_id_and_owner(job.id, owner.id)

    assert found is not None
    assert found.id == job.id


def test_get_by_id_and_owner_returns_none_for_a_different_owner(db_session):
    owner_a = _create_user(db_session, "alice")
    owner_b = _create_user(db_session, "bob")
    job = _create_job_for_owner(db_session, owner_a, filename="a1.mp4")
    repository = ProcessingJobRepository(db_session)

    found = repository.get_by_id_and_owner(job.id, owner_b.id)

    assert found is None


def test_cannot_create_a_second_active_job_for_the_same_video(db_session):
    """
    Real DB-level guarantee: at most one PENDING/RUNNING job per
    video (uq_processing_jobs_active_per_video), enforced so a future
    reprocess trigger (or a bug) can't silently create two workers
    racing to process the same video from two different job rows -
    claim_for_running()'s atomic claim only protects against
    redelivery of the *same* job_id, not this.
    """
    owner = _create_user(db_session)
    job = _create_job_for_owner(db_session, owner, status="PENDING", filename="a.mp4")

    db_session.add(
        ProcessingJob(video_id=job.video_id, job_type="transcription", status="RUNNING")
    )
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_completed_job_does_not_block_a_new_active_job(db_session):
    """
    The partial index only covers PENDING/RUNNING - a video with only
    terminal (COMPLETED/FAILED) history must still be able to get a
    new active job.
    """
    owner = _create_user(db_session)
    job = _create_job_for_owner(db_session, owner, status="COMPLETED", filename="a.mp4")

    new_job = ProcessingJob(
        video_id=job.video_id, job_type="transcription", status="PENDING",
    )
    db_session.add(new_job)
    db_session.commit()  # must not raise

    assert new_job.id is not None


def test_two_failed_jobs_for_the_same_video_do_not_collide(db_session):
    """
    Historical (terminal) rows are entirely outside the partial
    index's scope - unlike an active-job collision, there is no limit
    on how many FAILED/COMPLETED rows a video can accumulate.
    """
    owner = _create_user(db_session)
    job = _create_job_for_owner(db_session, owner, status="FAILED", filename="a.mp4")

    db_session.add(
        ProcessingJob(video_id=job.video_id, job_type="transcription", status="FAILED")
    )
    db_session.commit()  # must not raise


def test_concurrent_claim_only_one_worker_wins(tmp_path):
    """
    Two independent sessions, each with its OWN real SQLite
    connection (file-backed DB, not a shared in-memory connection),
    race to claim the same PENDING job via claim_for_running() from
    separate threads. A true multi-connection concurrency test, not
    two mocks and not two sessions time-sliced on one connection
    object (an in-memory StaticPool engine was tried first and
    produced a flaky `sqlite3.InterfaceError` from genuinely
    concurrent cursor use on one shared connection - a driver-level
    artifact of sharing a single connection object across threads,
    not a meaningful result. A file-backed DB with one connection per
    thread avoids that entirely while still exercising two real,
    independent database connections.

    Caveat, stated explicitly per the approved Phase 2 design: SQLite
    does not reproduce PostgreSQL's row-level locking semantics -
    SQLite serializes concurrent writers with a single database-level
    write lock, so this test proves claim_for_running()'s observable
    contract ("exactly one winner, no duplicate claim"), not
    PostgreSQL's specific row-locking mechanism.
    """
    db_path = tmp_path / "concurrent_claim.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    setup_session = SessionLocal()
    owner = _create_user(setup_session)
    job = _create_job_for_owner(setup_session, owner, status="PENDING", filename="a.mp4")
    job_id = job.id
    setup_session.close()
    engine.dispose()

    results: list[ProcessingJob | None] = [None, None]
    errors: list[Exception] = []

    def _claim(index: int) -> None:
        # Each thread opens its own engine/connection to the same
        # file-backed database, rather than sharing one connection
        # object across threads.
        thread_engine = create_engine(f"sqlite:///{db_path}")
        ThreadSessionLocal = sessionmaker(bind=thread_engine, autoflush=False, autocommit=False)
        session = ThreadSessionLocal()
        try:
            results[index] = ProcessingJobRepository(session).claim_for_running(job_id)
        except Exception as exc:  # pragma: no cover - surfaced via errors list
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
    final = ProcessingJobRepository(verify_session).get_by_id(job_id)
    assert final.status == "RUNNING"
    verify_session.close()
    verify_engine.dispose()


def test_claim_for_running_with_stale_after_seconds_still_claims_pending(db_session):
    """
    Passing stale_after_seconds must not change the existing PENDING
    claim behavior at all - it only adds a second, OR'd branch.
    """
    job = _create_job(db_session, status="PENDING")
    repository = ProcessingJobRepository(db_session)

    claimed = repository.claim_for_running(job.id, stale_after_seconds=3600)

    assert claimed is not None
    assert claimed.status == "RUNNING"


def test_claim_for_running_reclaims_a_stale_running_job(db_session):
    """
    Phase B fix: a job left RUNNING by a crashed worker (started
    longer ago than stale_after_seconds) must be reclaimable - before
    this, claim_for_running's WHERE clause only ever matched PENDING,
    so a crashed job was stuck RUNNING forever with no automatic
    recovery path.
    """
    job = _create_job(db_session, status="RUNNING")
    job.started_at = datetime.now(UTC) - timedelta(seconds=7200)
    db_session.commit()
    repository = ProcessingJobRepository(db_session)

    claimed = repository.claim_for_running(job.id, stale_after_seconds=3600)

    assert claimed is not None
    assert claimed.status == "RUNNING"
    assert claimed.started_at is not None


def test_claim_for_running_does_not_reclaim_a_genuinely_recent_running_job(db_session):
    """
    Safety-critical counterpart: a RUNNING job that started recently
    (well within stale_after_seconds) must never be reclaimed - it
    may still be genuinely, legitimately executing. Reclaiming it
    would risk two concurrent executions of the same job.
    """
    job = _create_job(db_session, status="RUNNING")
    job.started_at = datetime.now(UTC) - timedelta(seconds=5)
    db_session.commit()
    repository = ProcessingJobRepository(db_session)

    claimed = repository.claim_for_running(job.id, stale_after_seconds=3600)

    assert claimed is None

    reloaded = repository.get_by_id(job.id)
    assert reloaded.status == "RUNNING"


def test_claim_for_running_without_stale_after_seconds_never_reclaims_running(db_session):
    """
    Backward-compatibility check: omitting stale_after_seconds
    (the default, None) preserves the exact original behavior -
    PENDING-only, no RUNNING job is ever reclaimed regardless of age.
    """
    job = _create_job(db_session, status="RUNNING")
    job.started_at = datetime.now(UTC) - timedelta(days=1)
    db_session.commit()
    repository = ProcessingJobRepository(db_session)

    claimed = repository.claim_for_running(job.id)

    assert claimed is None


# --- Orphaned-dispatch reconciliation (dual-write gap fix) ---------------
#
# Regression coverage for the exact defect that left jobs 5/13
# orphaned PENDING forever: UploadPipeline.process commits a
# ProcessingJob row, then calls process_video.delay() with no guard.
# If that call never arrives, the row is PENDING with started_at
# still NULL, indistinguishable from "dispatch just happened a moment
# ago" without a created_at column to measure its age against.


def test_get_orphaned_pending_finds_old_unstarted_job(db_session):
    job = _create_job(db_session, status="PENDING")
    job.created_at = datetime.now(UTC) - timedelta(seconds=600)
    db_session.commit()
    repository = ProcessingJobRepository(db_session)

    found = repository.get_orphaned_pending(
        video_id=job.video_id, older_than_seconds=300,
    )

    assert [j.id for j in found] == [job.id]


def test_get_orphaned_pending_ignores_a_recently_created_pending_job(db_session):
    """
    A PENDING job created moments ago is NOT orphaned - its dispatch
    may simply still be in flight. created_at defaults to "now", so
    no manipulation is needed here.
    """
    job = _create_job(db_session, status="PENDING")
    repository = ProcessingJobRepository(db_session)

    found = repository.get_orphaned_pending(
        video_id=job.video_id, older_than_seconds=300,
    )

    assert found == []


def test_get_orphaned_pending_ignores_a_job_that_was_actually_started(db_session):
    """
    started_at being set at all means some worker DID pick it up -
    even if it's since gone stale/RUNNING-crashed, that's
    claim_for_running's stale-RUNNING reclaim's job, not this one's.
    A PENDING job with started_at set is not a state this repository
    method should ever see in practice, but must not be misidentified
    as orphaned if it somehow is.
    """
    job = _create_job(db_session, status="PENDING")
    job.created_at = datetime.now(UTC) - timedelta(seconds=600)
    job.started_at = datetime.now(UTC) - timedelta(seconds=600)
    db_session.commit()
    repository = ProcessingJobRepository(db_session)

    found = repository.get_orphaned_pending(
        video_id=job.video_id, older_than_seconds=300,
    )

    assert found == []


def test_get_orphaned_pending_ignores_other_videos(db_session):
    owner = _create_user(db_session)
    job_a = _create_job_for_owner(db_session, owner, status="PENDING", filename="a.mp4")
    job_a.created_at = datetime.now(UTC) - timedelta(seconds=600)
    job_b = _create_job_for_owner(db_session, owner, status="PENDING", filename="b.mp4")
    job_b.created_at = datetime.now(UTC) - timedelta(seconds=600)
    db_session.commit()
    repository = ProcessingJobRepository(db_session)

    found = repository.get_orphaned_pending(
        video_id=job_a.video_id, older_than_seconds=300,
    )

    assert [j.id for j in found] == [job_a.id]


def test_get_all_orphaned_pending_finds_jobs_across_every_video(db_session):
    owner = _create_user(db_session)
    job_a = _create_job_for_owner(db_session, owner, status="PENDING", filename="a.mp4")
    job_a.created_at = datetime.now(UTC) - timedelta(seconds=600)
    job_b = _create_job_for_owner(db_session, owner, status="PENDING", filename="b.mp4")
    job_b.created_at = datetime.now(UTC) - timedelta(seconds=600)
    db_session.commit()
    repository = ProcessingJobRepository(db_session)

    found = repository.get_all_orphaned_pending(older_than_seconds=300, limit=50)

    assert {j.id for j in found} == {job_a.id, job_b.id}


def test_get_all_orphaned_pending_respects_limit(db_session):
    owner = _create_user(db_session)
    for i in range(3):
        job = _create_job_for_owner(
            db_session, owner, status="PENDING", filename=f"limit-{i}.mp4",
        )
        job.created_at = datetime.now(UTC) - timedelta(seconds=600)
    db_session.commit()
    repository = ProcessingJobRepository(db_session)

    found = repository.get_all_orphaned_pending(older_than_seconds=300, limit=2)

    assert len(found) == 2


def test_claim_for_dispatch_retry_increments_attempts_on_eligible_job(db_session):
    job = _create_job(db_session, status="PENDING")
    assert job.dispatch_attempts == 1
    repository = ProcessingJobRepository(db_session)

    claimed = repository.claim_for_dispatch_retry(job.id)

    assert claimed is not None
    assert claimed.dispatch_attempts == 2
    # Still PENDING - this only tracks attempts, the actual claim to
    # RUNNING is claim_for_running's job once a dispatched task runs.
    assert claimed.status == "PENDING"


def test_claim_for_dispatch_retry_returns_none_once_job_has_started(db_session):
    """
    If the job was claimed (started_at set) between the caller
    reading it as orphaned and calling this - e.g. a redelivered
    original task message finally arrived - this must not re-dispatch
    a second time.
    """
    job = _create_job(db_session, status="RUNNING")
    job.started_at = datetime.now(UTC)
    db_session.commit()
    repository = ProcessingJobRepository(db_session)

    claimed = repository.claim_for_dispatch_retry(job.id)

    assert claimed is None


# --- Manual retry (FAILED -> PENDING) ------------------------------------


def test_claim_for_retry_transitions_failed_job_to_pending(db_session):
    job = _create_job(db_session, status="FAILED")
    job.started_at = datetime.now(UTC) - timedelta(minutes=10)
    job.finished_at = datetime.now(UTC) - timedelta(minutes=9)
    job.error_message = "something went wrong"
    job.progress = 100
    job.current_step = "Failed"
    job.dispatch_attempts = 2
    db_session.commit()
    repository = ProcessingJobRepository(db_session)

    claimed = repository.claim_for_retry(job.id)

    assert claimed is not None
    assert claimed.status == "PENDING"
    # Looks exactly like a freshly-created job - no stale data from
    # the previous failed attempt leaks through.
    assert claimed.started_at is None
    assert claimed.finished_at is None
    assert claimed.error_message is None
    assert claimed.progress == 0
    assert claimed.current_step is None
    assert claimed.dispatch_attempts == 1


def test_claim_for_retry_does_not_claim_a_non_failed_job(db_session):
    job = _create_job(db_session, status="RUNNING")
    repository = ProcessingJobRepository(db_session)

    claimed = repository.claim_for_retry(job.id)

    assert claimed is None
    reloaded = repository.get_by_id(job.id)
    assert reloaded.status == "RUNNING"


def test_claim_for_retry_two_concurrent_requests_only_one_wins(db_session):
    """
    Same atomic-UPDATE guarantee as claim_for_running: a double click
    on "retry" must never dispatch the same job twice.
    """
    job = _create_job(db_session, status="FAILED")
    repository = ProcessingJobRepository(db_session)

    first = repository.claim_for_retry(job.id)
    second = repository.claim_for_retry(job.id)

    assert first is not None
    assert second is None


def test_claim_for_dispatch_retry_stops_once_a_real_claim_wins(db_session):
    """
    Unlike claim_for_running's PENDING->RUNNING transition, this
    method deliberately does not change status - two reconciliation
    calls in a row both legitimately increment the counter (bounding
    retries is ProcessingJobService.reconcile_orphaned_dispatch's
    job, via settings.celery.max_dispatch_attempts, not this
    method's). What this method must guarantee is narrower: once the
    job is actually claimed by a real task execution (started_at
    set, exactly what claim_for_running's own atomic UPDATE already
    protects with its own concurrent-caller test), this method stops
    matching it at all - a job already being genuinely processed is
    never treated as still orphaned.
    """
    job = _create_job(db_session, status="PENDING")
    repository = ProcessingJobRepository(db_session)

    first = repository.claim_for_dispatch_retry(job.id)
    assert first is not None
    assert first.dispatch_attempts == 2

    # A real task execution now claims the job for real.
    repository.claim_for_running(job.id)

    second = repository.claim_for_dispatch_retry(job.id)
    assert second is None
