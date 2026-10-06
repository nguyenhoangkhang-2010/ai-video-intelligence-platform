from sqlalchemy.orm import Session

from app.models.embedding import Embedding
from app.repositories.base import BaseRepository


class EmbeddingRepository(BaseRepository[Embedding]):
    """Repository for Embedding model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Embedding,
        )

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Embedding]:

        return (
            self.db.query(Embedding)
            .filter(Embedding.video_id == video_id)
            .order_by(Embedding.chunk_index)
            .all()
        )

    def get_by_vector_id(
        self,
        vector_id: str,
    ) -> Embedding | None:

        return (
            self.db.query(Embedding)
            .filter(Embedding.vector_id == vector_id)
            .first()
        )

    def delete_by_video_id(
        self,
        video_id: int,
    ) -> None:
        """
        Bulk-delete all embeddings belonging to a video in a single
        statement/commit (used when replacing a video's embeddings).
        """

        (
            self.db.query(Embedding)
            .filter(Embedding.video_id == video_id)
            .delete(synchronize_session=False)
        )

        self.db.commit()

    def replace_for_video(
        self,
        video_id: int,
        new_embeddings: list[Embedding],
    ) -> list[Embedding]:
        """
        Atomically replace every embedding row for `video_id`: delete
        the old rows and insert `new_embeddings` in one transaction.

        Used by the embedding pipeline stage AFTER the FAISS write
        already succeeded (see VideoPipelineService.embedding_stage),
        so this is the one DB-side step that can still fail for that
        video. A single commit means it can only ever land in one of
        two states - every old row gone and every new row present, or
        (on any failure, via the rollback below) every old row still
        exactly as it was - never the previous partial-insert-loop
        failure mode where some new rows existed and others didn't.
        """

        try:
            (
                self.db.query(Embedding)
                .filter(Embedding.video_id == video_id)
                .delete(synchronize_session=False)
            )

            self.db.add_all(new_embeddings)
            self.db.commit()

            for embedding in new_embeddings:
                self.db.refresh(embedding)

            return new_embeddings
        except Exception:
            self.db.rollback()
            raise