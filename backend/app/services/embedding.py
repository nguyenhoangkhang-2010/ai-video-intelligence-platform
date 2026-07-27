from app.models.embedding import Embedding
from app.repositories.embedding import EmbeddingRepository
from app.schemas.embedding import EmbeddingCreate


class EmbeddingService:
    """Service for Embedding operations."""

    def __init__(
        self,
        repository: EmbeddingRepository,
    ):
        self.repository = repository

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[Embedding]:
        """
        Get all embeddings of a video.
        """
        return self.repository.get_by_video_id(
            video_id,
        )

    def get_by_vector_id(
        self,
        vector_id: str,
    ) -> Embedding | None:
        """
        Get embedding by vector id.
        """
        return self.repository.get_by_vector_id(
            vector_id,
        )

    def create_embedding(
        self,
        embedding_data: EmbeddingCreate,
    ) -> Embedding:
        """
        Create embedding if it does not already exist.
        """
        existing = self.repository.get_by_vector_id(
            embedding_data.vector_id,
        )

        if existing is not None:
            return existing

        embedding = Embedding(
            **embedding_data.model_dump(),
        )

        return self.repository.create(
            embedding,
        )

    def save_embedding(
        self,
        embedding_data: EmbeddingCreate,
    ) -> Embedding:
        """
        Create or update embedding.
        """
        embedding = self.repository.get_by_vector_id(
            embedding_data.vector_id,
        )

        if embedding is None:
            embedding = Embedding(
                **embedding_data.model_dump(),
            )
            return self.repository.create(
                embedding,
            )
            
        embedding.chunk_text = embedding_data.chunk_text
        embedding.embedding_model = embedding_data.embedding_model

        return self.repository.update(
            embedding,
        )