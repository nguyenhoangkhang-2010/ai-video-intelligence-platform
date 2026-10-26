from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base


class Embedding(Base):
    """Embedding ORM model."""

    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    video_id: Mapped[int] = mapped_column(
        ForeignKey(
            "videos.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    vector_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    # The span of video (seconds) this chunk's text was spoken in,
    # derived from the transcript's timed segments at embedding time
    # (see ai.embedding.timing). NULL for chunks embedded before
    # segments were stored, or when the transcript has none.
    start_time: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    end_time: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Where the chunk's text came from: "speech" (transcript) or
    # "visual" (on-screen text/description of a visual segment).
    # Search results and RAG citations are labelled with it, so an
    # answer never presents something shown on screen as something
    # that was said, or vice versa.
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
        back_populates="embeddings",
    )