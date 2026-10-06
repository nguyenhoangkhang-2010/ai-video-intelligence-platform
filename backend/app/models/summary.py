from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base

class Summary(Base):
    """Summary ORM model."""

    __tablename__ = "summaries"
    __table_args__ = (
        # One summary per (video, type) - SummaryService.save_summary
        # is the only write path the pipeline uses (video_pipeline.py
        # summary_stage), and it already upserts on this exact key;
        # this constraint is what makes that upsert correct under a
        # genuine concurrent write too, not just in the common
        # single-writer case.
        UniqueConstraint(
            "video_id", "type",
            name="uq_summaries_video_id_type",
        ),
    )

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

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    video = relationship(
        "Video",
        back_populates="summaries",
    )