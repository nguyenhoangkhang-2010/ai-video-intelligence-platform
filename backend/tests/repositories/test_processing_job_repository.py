from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.models.video import Video
from app.repositories.processing_job import ProcessingJobRepository


def _create_job(db_session, status: str = "PENDING") -> ProcessingJob:
    """
    Create a real ProcessingJob row (with its required User/Video
    parents) directly against the fixture's schema.
    """
    user = User(
        username="owner",
        email="owner@example.com",
        hashed_password="hashed",
    )
    db_session.add(user)
    db_session.commit()

    video = Video(
        owner_id=user.id,
        title="Sample video",
        filename=f"video-{status}.mp4",
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
