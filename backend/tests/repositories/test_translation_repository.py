import pytest
from sqlalchemy.exc import IntegrityError

from app.models.translation import Translation
from app.models.user import User
from app.models.video import Video
from app.repositories.translation import TranslationRepository
from app.schemas.translation import TranslationCreate
from app.services.translation import TranslationService


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


def test_unique_constraint_rejects_duplicate_video_id_and_language(db_session):
    """
    Real DB-level guarantee behind TranslationService.save_translation's
    upsert: a genuine duplicate (video_id, language) insert must be
    rejected by the database itself, not only by an application-level
    check-then-insert that a concurrent writer could race past.
    """
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")

    db_session.add(Translation(video_id=video.id, language="en", subtitle="first"))
    db_session.commit()

    db_session.add(Translation(video_id=video.id, language="en", subtitle="second"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_save_translation_replaces_subtitle_on_reprocess(db_session):
    """
    Reprocessing a video must regenerate its translation for that
    language, not silently keep the first attempt's text.
    """
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    repository = TranslationRepository(db_session)
    service = TranslationService(repository)

    first = service.save_translation(
        TranslationCreate(video_id=video.id, language="en", subtitle="first attempt")
    )

    second = service.save_translation(
        TranslationCreate(video_id=video.id, language="en", subtitle="second attempt")
    )

    assert first.id == second.id

    remaining = repository.get_by_video_id(video.id)
    assert len(remaining) == 1
    assert remaining[0].subtitle == "second attempt"


def test_save_translation_keeps_languages_independent(db_session):
    """
    Two different languages for the same video are two distinct
    logical artifacts, not a collision on the unique constraint.
    """
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    repository = TranslationRepository(db_session)
    service = TranslationService(repository)

    service.save_translation(
        TranslationCreate(video_id=video.id, language="en", subtitle="english")
    )
    service.save_translation(
        TranslationCreate(video_id=video.id, language="fr", subtitle="french")
    )

    remaining = {row.language: row.subtitle for row in repository.get_by_video_id(video.id)}
    assert remaining == {"en": "english", "fr": "french"}
