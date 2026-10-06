import pytest
from sqlalchemy.exc import IntegrityError

from app.models.embedding import Embedding
from app.models.user import User
from app.models.video import Video
from app.repositories.embedding import EmbeddingRepository


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


def _create_embedding(db_session, video: Video, vector_id: str, chunk_index: int = 0) -> Embedding:
    embedding = Embedding(
        video_id=video.id,
        chunk_index=chunk_index,
        chunk_text=f"chunk {chunk_index} text",
        embedding_model="BAAI/bge-m3",
        vector_id=vector_id,
    )
    db_session.add(embedding)
    db_session.commit()
    return embedding


def test_replace_for_video_atomically_swaps_old_rows_for_new_ones(db_session):
    owner = _create_user(db_session)
    video = _create_video(db_session, owner, filename="a.mp4")
    _create_embedding(db_session, video, vector_id="old-1", chunk_index=0)
    _create_embedding(db_session, video, vector_id="old-2", chunk_index=1)

    repository = EmbeddingRepository(db_session)

    new_rows = [
        Embedding(
            video_id=video.id,
            chunk_index=0,
            chunk_text="new chunk zero",
            embedding_model="BAAI/bge-m3",
            vector_id="new-1",
        ),
    ]

    result = repository.replace_for_video(video.id, new_rows)

    assert [row.vector_id for row in result] == ["new-1"]
    assert result[0].id is not None  # refreshed with a real PK

    remaining = repository.get_by_video_id(video.id)
    assert {row.vector_id for row in remaining} == {"new-1"}


def test_replace_for_video_rolls_back_cleanly_on_failure(db_session):
    """
    Failure injection: the new row's vector_id collides with another
    video's still-existing row, violating the unique constraint on
    Embedding.vector_id. The whole operation (delete-old + insert-new)
    must roll back as one unit - video A's original row must still be
    present afterward, not deleted-and-never-replaced.
    """
    owner = _create_user(db_session)
    video_a = _create_video(db_session, owner, filename="a.mp4")
    video_b = _create_video(db_session, owner, filename="b.mp4")

    _create_embedding(db_session, video_a, vector_id="keep-this", chunk_index=0)
    _create_embedding(db_session, video_b, vector_id="already-exists", chunk_index=0)

    repository = EmbeddingRepository(db_session)

    colliding_row = Embedding(
        video_id=video_a.id,
        chunk_index=0,
        chunk_text="would-be new chunk",
        embedding_model="BAAI/bge-m3",
        vector_id="already-exists",  # already used by video_b's row
    )

    with pytest.raises(IntegrityError):
        repository.replace_for_video(video_a.id, [colliding_row])

    # Rolled back: video A's original row is still exactly as it was,
    # never left deleted-without-replacement.
    remaining_a = repository.get_by_video_id(video_a.id)
    assert {row.vector_id for row in remaining_a} == {"keep-this"}

    # The other video's row is untouched throughout.
    remaining_b = repository.get_by_video_id(video_b.id)
    assert {row.vector_id for row in remaining_b} == {"already-exists"}
