from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base


class Video(Base):
    """Video ORM model."""

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    language: Mapped[str] = mapped_column(
        String(20),
        default="unknown",
    )

    duration: Mapped[int] = mapped_column(
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="uploaded",
        index=True,
    )

    # Storage key for a real, ffmpeg-extracted representative frame
    # (see app/utils/thumbnail.py), not a filesystem path - resolved
    # through the same StorageBackend the uploaded file itself is
    # served through (GET /videos/{id}/thumbnail). Nullable: existing
    # videos have none until backfilled, and extraction is allowed to
    # fail without failing the rest of the pipeline (see
    # VideoPipelineService.metadata_stage).
    thumbnail_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    @property
    def has_thumbnail(self) -> bool:
        """
        Exposed to the API (see VideoRead) instead of `thumbnail_key`
        itself, so the frontend can decide whether to render
        GET /videos/{id}/thumbnail without ever seeing the storage key.
        """
        return self.thumbnail_key is not None

    owner_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    owner = relationship(
        "User",
        back_populates="videos",
    )
    
    transcript = relationship(
        "Transcript",
        back_populates="video",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    summaries = relationship(
        "Summary",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    chapters = relationship(
        "Chapter",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    embeddings = relationship(
        "Embedding",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    translations = relationship(
        "Translation",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    flashcards = relationship(
        "Flashcard",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    quizzes = relationship(
        "Quiz",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    processing_jobs = relationship(
        "ProcessingJob",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
    chat_histories = relationship(
        "ChatHistory",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )