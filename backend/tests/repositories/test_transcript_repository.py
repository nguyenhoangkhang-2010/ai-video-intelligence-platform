import pytest
from sqlalchemy.exc import IntegrityError

from app.models.transcript import Transcript
from app.models.user import User
from app.models.video import Video
from app.repositories.transcript import TranscriptRepository
from app.schemas.transcript import TranscriptCreate
from app.services.transcript import TranscriptService


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


def test_unique_constraint_rejects_a_second_transcript_for_the_same_video(db_session):
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")

    db_session.add(Transcript(video_id=video.id, language="en", text="first"))
    db_session.commit()

    db_session.add(Transcript(video_id=video.id, language="en", text="second"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_save_transcript_replaces_text_on_reprocess(db_session):
    """
    Reprocessing a video must regenerate its transcript, not silently
    keep whatever the first attempt produced (video_pipeline.py's
    transcription_stage now calls save_transcript, not
    create_transcript, specifically for this reason).
    """
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    repository = TranscriptRepository(db_session)
    service = TranscriptService(repository)

    first = service.save_transcript(
        TranscriptCreate(video_id=video.id, language="en", text="first attempt")
    )

    second = service.save_transcript(
        TranscriptCreate(video_id=video.id, language="fr", text="second attempt, longer text")
    )

    assert first.id == second.id

    reloaded = repository.get_by_video_id(video.id)
    assert reloaded.text == "second attempt, longer text"
    assert reloaded.language == "fr"
    assert reloaded.word_count == len("second attempt, longer text".split())
