import pytest
from sqlalchemy.exc import IntegrityError

from app.models.flashcard import Flashcard
from app.models.user import User
from app.models.video import Video
from app.repositories.flashcard import FlashcardRepository


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


def _create_flashcard(db_session, video: Video, question: str) -> Flashcard:
    flashcard = Flashcard(
        video_id=video.id,
        question=question,
        answer="Back",
        difficulty="medium",
    )
    db_session.add(flashcard)
    db_session.commit()
    return flashcard


def test_replace_for_video_atomically_swaps_old_rows_for_new_ones(db_session):
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    _create_flashcard(db_session, video, question="Old front 1")
    _create_flashcard(db_session, video, question="Old front 2")

    repository = FlashcardRepository(db_session)

    new_rows = [
        Flashcard(video_id=video.id, question="New front", answer="New back"),
    ]

    result = repository.replace_for_video(video.id, new_rows)

    assert [row.question for row in result] == ["New front"]
    assert result[0].id is not None

    remaining = repository.get_by_video_id(video.id)
    assert {row.question for row in remaining} == {"New front"}


def test_replace_for_video_with_empty_list_clears_old_rows(db_session):
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    _create_flashcard(db_session, video, question="Stale front")

    repository = FlashcardRepository(db_session)

    result = repository.replace_for_video(video.id, [])

    assert result == []
    assert repository.get_by_video_id(video.id) == []


def test_replace_for_video_rolls_back_cleanly_on_failure(db_session):
    """
    Failure injection: one of the new rows violates a real DB
    constraint (NOT NULL on answer). The whole operation must roll
    back as one unit - the video's original flashcards must still be
    present afterward.
    """
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    _create_flashcard(db_session, video, question="Keep me")

    repository = FlashcardRepository(db_session)

    invalid_row = Flashcard(
        video_id=video.id,
        question="Would-be new",
        answer=None,  # violates NOT NULL
    )

    with pytest.raises(IntegrityError):
        repository.replace_for_video(video.id, [invalid_row])

    remaining = repository.get_by_video_id(video.id)
    assert {row.question for row in remaining} == {"Keep me"}
