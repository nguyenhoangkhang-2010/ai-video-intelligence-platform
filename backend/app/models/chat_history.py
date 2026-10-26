from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base


class ChatHistory(Base):
    """Chat history ORM model."""

    __tablename__ = "chat_histories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    video_id: Mapped[int] = mapped_column(
        ForeignKey(
            "videos.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # JSON-serialized list[SearchResult] (see app/schemas/search.py) -
    # the retrieved chunks this answer was actually grounded in, kept
    # so a reloaded history entry can still show real citations rather
    # than silently losing them. Serialized/deserialized in
    # ChatHistoryService, same convention as Quiz.options (a Text
    # column for structured-but-simple data, not a new JSON column
    # type this codebase doesn't otherwise use).
    sources: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    user = relationship(
        "User",
        back_populates="chat_histories",
    )

    video = relationship(
        "Video",
        back_populates="chat_histories",
    )