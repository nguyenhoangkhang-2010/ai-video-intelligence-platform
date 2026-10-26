import json

from app.models.chat_history import ChatHistory
from app.repositories.chat_history import ChatHistoryRepository
from app.schemas.chat_history import ChatHistoryRead
from app.schemas.search import SearchResult


class ChatHistoryService:
    """
    Service for ChatHistory operations.

    One row per real, answered RAG turn (see app/api/v1/endpoints/
    search.py::ask_video) - never written for empty_query/no_embeddings/
    no_relevant_chunks, since there is no real question+answer pair to
    record for those. Recording is best-effort from the caller's side
    (a write failure here must never break the RAG response itself).
    """

    def __init__(
        self,
        repository: ChatHistoryRepository,
    ):
        self.repository = repository

    def record(
        self,
        user_id: int,
        video_id: int,
        question: str,
        answer: str,
        sources: list[SearchResult],
    ) -> ChatHistory:
        entry = ChatHistory(
            user_id=user_id,
            video_id=video_id,
            question=question,
            answer=answer,
            sources=(
                json.dumps([source.model_dump() for source in sources])
                if sources
                else None
            ),
        )

        return self.repository.create(
            entry,
        )

    def get_by_user_and_video(
        self,
        user_id: int,
        video_id: int,
    ) -> list[ChatHistoryRead]:
        """
        Oldest first - the order a chat transcript actually reads in,
        unlike the repository's own newest-first ordering (which suits
        a "recent activity" list, not a conversation replay).
        """
        rows = list(
            reversed(
                self.repository.get_by_user_and_video(
                    user_id=user_id,
                    video_id=video_id,
                ),
            ),
        )

        return [self._to_read(row) for row in rows]

    @staticmethod
    def _to_read(row: ChatHistory) -> ChatHistoryRead:
        sources = json.loads(row.sources) if row.sources else []

        return ChatHistoryRead(
            id=row.id,
            user_id=row.user_id,
            video_id=row.video_id,
            question=row.question,
            answer=row.answer,
            sources=[SearchResult(**source) for source in sources],
            created_at=row.created_at,
        )
