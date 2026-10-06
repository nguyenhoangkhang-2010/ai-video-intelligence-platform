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


class Translation(Base):
    """Translation ORM model."""

    __tablename__ = "translations"
    __table_args__ = (
        # One translation per (video, language) - TranslationService.
        # save_translation is the only write path the pipeline uses
        # (video_pipeline.py translation_stage), and it already
        # upserts on this exact key; this constraint is what makes
        # that upsert correct under a genuine concurrent write too,
        # not just in the common single-writer case.
        UniqueConstraint(
            "video_id", "language",
            name="uq_translations_video_id_language",
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

    language: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    subtitle: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    video = relationship(
        "Video",
        back_populates="translations",
    )