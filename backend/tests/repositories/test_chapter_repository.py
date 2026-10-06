import pytest
from sqlalchemy.exc import IntegrityError

from app.models.chapter import Chapter
from app.models.user import User
from app.models.video import Video
from app.repositories.chapter import ChapterRepository


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


def _create_chapter(db_session, video: Video, title: str) -> Chapter:
    chapter = Chapter(
        video_id=video.id,
        title=title,
        start_time=0.0,
        end_time=5.0,
    )
    db_session.add(chapter)
    db_session.commit()
    return chapter


def test_replace_for_video_atomically_swaps_old_rows_for_new_ones(db_session):
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    _create_chapter(db_session, video, title="Old chapter 1")
    _create_chapter(db_session, video, title="Old chapter 2")

    repository = ChapterRepository(db_session)

    new_rows = [
        Chapter(video_id=video.id, title="New chapter", start_time=0.0, end_time=10.0),
    ]

    result = repository.replace_for_video(video.id, new_rows)

    assert [row.title for row in result] == ["New chapter"]
    assert result[0].id is not None  # refreshed with a real PK

    remaining = repository.get_by_video_id(video.id)
    assert {row.title for row in remaining} == {"New chapter"}


def test_replace_for_video_with_empty_list_clears_old_rows(db_session):
    """
    Zero chapters detected is a valid, non-error outcome (see
    VideoPipelineService.chapter_stage's docstring) - replacing with
    an empty list must still atomically clear stale chapters from a
    previous attempt.
    """
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    _create_chapter(db_session, video, title="Stale chapter")

    repository = ChapterRepository(db_session)

    result = repository.replace_for_video(video.id, [])

    assert result == []
    assert repository.get_by_video_id(video.id) == []


def test_replace_for_video_rolls_back_cleanly_on_failure(db_session):
    """
    Failure injection: one of the new rows violates a real DB
    constraint (NOT NULL on title). The whole operation (delete-old +
    insert-new) must roll back as one unit - the video's original
    chapters must still be present afterward, never deleted-and-
    never-replaced.
    """
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    _create_chapter(db_session, video, title="Keep me")

    repository = ChapterRepository(db_session)

    invalid_row = Chapter(
        video_id=video.id,
        title=None,  # violates NOT NULL
        start_time=0.0,
        end_time=1.0,
    )

    with pytest.raises(IntegrityError):
        repository.replace_for_video(video.id, [invalid_row])

    remaining = repository.get_by_video_id(video.id)
    assert {row.title for row in remaining} == {"Keep me"}
