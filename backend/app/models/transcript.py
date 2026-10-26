from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
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

    # Whisper's timed segments - [{"start", "end", "text", "speaker"?}]
    # in video seconds, in order. Powers the click-to-seek transcript,
    # the timestamps on search results / chat citations (via the
    # embedding chunk times derived from these), and chapter
    # detection on resume. NULL for transcripts saved before segments
    # were stored.
    segments: Mapped[list[dict] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # "speech" (Whisper) or "visual": a video with no speech gets a
    # transcript built from what is on screen (ai.vision) instead of
    # failing processing.
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="speech",
        server_default="speech",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    video = relationship(
        "Video",
        back_populates="transcript",
    )