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