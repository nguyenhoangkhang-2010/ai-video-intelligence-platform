import pytest
from sqlalchemy.exc import IntegrityError

from app.models.summary import Summary
from app.models.user import User
from app.models.video import Video
from app.repositories.summary import SummaryRepository
from app.schemas.summary import SummaryCreate
from app.services.summary import SummaryService


def _create_user(db_session, username: str = "owner") -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="hashed",
    )
    db_session.add(user)
    db_session.commit()
    return user


def _create_video(db_session, owner: User, filename: str) -> Video:
    video = Video(
        owner_id=owner.id,
        title="Sample video",
        filename=filename,
        language="en",
        duration=60,
        status="processing",
    )
    db_session.add(video)
    db_session.commit()
    return video


def test_unique_constraint_rejects_duplicate_video_id_and_type(db_session):
    """
    Real DB-level guarantee behind SummaryService.save_summary's
    upsert: a genuine duplicate (video_id, type) insert must be
    rejected by the database itself, not only by an application-level
    check-then-insert that a concurrent writer could race past.
    """
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")

    db_session.add(
        Summary(video_id=video.id, type="default", content="first", model_name="m1")
    )
    db_session.commit()

    db_session.add(
        Summary(video_id=video.id, type="default", content="second", model_name="m1")
    )
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_save_summary_replaces_content_on_reprocess(db_session):
    """
    Reprocessing a video must regenerate its summary, not silently
    keep the first attempt's content (LLM output is not deterministic
    across retries - idempotency here means "one logical attempt, one
    persisted artifact," not "identical text every time").
    """
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    repository = SummaryRepository(db_session)
    service = SummaryService(repository)

    first = service.save_summary(
        SummaryCreate(video_id=video.id, type="default", content="first attempt", model_name="m1")
    )

    second = service.save_summary(
        SummaryCreate(video_id=video.id, type="default", content="second attempt", model_name="m2")
    )

    # Same logical row (same PK), content/model replaced in place.
    assert first.id == second.id

    remaining = repository.get_by_video_id(video.id)
    assert len(remaining) == 1
    assert remaining[0].content == "second attempt"
    assert remaining[0].model_name == "m2"
