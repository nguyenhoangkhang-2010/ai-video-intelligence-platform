import pytest
from sqlalchemy.exc import IntegrityError

from app.models.quiz import Quiz
from app.models.user import User
from app.models.video import Video
from app.repositories.quiz import QuizRepository


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


def _create_quiz(db_session, video: Video, question: str) -> Quiz:
    quiz = Quiz(
        video_id=video.id,
        type="multiple_choice",
        question=question,
        answer="A",
        options="A,B,C,D",
    )
    db_session.add(quiz)
    db_session.commit()
    return quiz


def test_replace_for_video_atomically_swaps_old_rows_for_new_ones(db_session):
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    _create_quiz(db_session, video, question="Old Q1?")
    _create_quiz(db_session, video, question="Old Q2?")

    repository = QuizRepository(db_session)

    new_rows = [
        Quiz(video_id=video.id, type="true_false", question="New Q?", answer="True"),
    ]

    result = repository.replace_for_video(video.id, new_rows)

    assert [row.question for row in result] == ["New Q?"]
    assert result[0].id is not None

    remaining = repository.get_by_video_id(video.id)
    assert {row.question for row in remaining} == {"New Q?"}


def test_replace_for_video_with_empty_list_clears_old_rows(db_session):
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    _create_quiz(db_session, video, question="Stale Q?")

    repository = QuizRepository(db_session)

    result = repository.replace_for_video(video.id, [])

    assert result == []
    assert repository.get_by_video_id(video.id) == []


def test_replace_for_video_rolls_back_cleanly_on_failure(db_session):
    """
    Failure injection: one of the new rows violates a real DB
    constraint (NOT NULL on question). The whole operation must roll
    back as one unit - the video's original quizzes must still be
    present afterward.
    """
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    _create_quiz(db_session, video, question="Keep me?")

    repository = QuizRepository(db_session)

    invalid_row = Quiz(
        video_id=video.id,
        type="multiple_choice",
        question=None,  # violates NOT NULL
        answer="A",
    )

    with pytest.raises(IntegrityError):
        repository.replace_for_video(video.id, [invalid_row])

    remaining = repository.get_by_video_id(video.id)
    assert {row.question for row in remaining} == {"Keep me?"}
