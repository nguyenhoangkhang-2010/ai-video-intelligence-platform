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
