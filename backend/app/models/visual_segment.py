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


class VisualSegment(Base):
    """
    A span of video showing the same thing on screen, as read by the
    vision model (ai.vision): the words visible on screen and a short
    description of the picture, plus the keyframe it came from.
    """

    __tablename__ = "visual_segments"

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
        index=True,
    )

    start_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    end_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Storage key of the keyframe JPEG (frames/{video_id}/{n}.jpg).
    frame_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    on_screen_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    # Cosine similarity between this segment and what was said while
    # it was on screen (BGE-M3). NULL when nothing was said then, or
    # before the embedding stage has run.
    speech_similarity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    video = relationship(
        "Video",
        back_populates="visual_segments",
    )
