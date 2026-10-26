from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory
from app.repositories.base import BaseRepository


class ChatHistoryRepository(BaseRepository[ChatHistory]):
    """Repository for ChatHistory model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=ChatHistory,
        )

    def get_by_user_id(
        self,
        user_id: int,
    ) -> list[ChatHistory]:

        return (
            self.db.query(ChatHistory)
            .filter(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc())
            .all()
        )

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[ChatHistory]:

        return (
            self.db.query(ChatHistory)
            .filter(ChatHistory.video_id == video_id)
            .order_by(ChatHistory.created_at.desc())
            .all()
        )

    def get_by_user_and_video(
        self,
        user_id: int,
        video_id: int,
    ) -> list[ChatHistory]:

        return (
            self.db.query(ChatHistory)
            .filter(
                ChatHistory.user_id == user_id,
                ChatHistory.video_id == video_id,
            )
            .order_by(ChatHistory.created_at.desc())
            .all()
        )