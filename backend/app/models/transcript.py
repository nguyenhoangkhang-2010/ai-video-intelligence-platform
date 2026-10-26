from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base

class Transcript(Base):
    """Transcript ORM model."""

    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    video_id: Mapped[int] = mapped_column(
        ForeignKey(
            "videos.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    language: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    word_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    video = relationship(
        "Video",
        back_populates="transcript",
    )