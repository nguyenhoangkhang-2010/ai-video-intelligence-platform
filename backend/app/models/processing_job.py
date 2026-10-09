from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base


class ProcessingJob(Base):
    """Processing job ORM model."""

    __tablename__ = "processing_jobs"
    __table_args__ = (
        # At most one active (PENDING/RUNNING) job per video, enforced
        # at the database level rather than relying on there simply
        # being no code path today that creates a second one.
        # COMPLETED/FAILED jobs are deliberately excluded from this
        # index (via the partial WHERE clause) so processing history
        # is never blocked or constrained by it - only concurrently
        # *active* work is. claim_for_running()'s existing atomic
        # PENDING->RUNNING UPDATE still governs same-job redelivery;
        # this index governs a different video_id-level invariant
        # entirely (two distinct job rows for the same video).
        Index(
            "uq_processing_jobs_active_per_video",
            "video_id",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'RUNNING')"),
            sqlite_where=text("status IN ('PENDING', 'RUNNING')"),
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

    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        nullable=False,
        index=True,
    )
    
    progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Set once at creation (BaseRepository.create commits+refreshes,
    # so the DB's CURRENT_TIMESTAMP default round-trips onto this
    # column immediately). Distinguishes "this PENDING job is a few
    # seconds old, dispatch is probably still in flight" from "this
    # PENDING job is minutes/hours old with no started_at - dispatch
    # likely never happened" - see
    # ProcessingJobService.reconcile_orphaned_dispatch.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    # Bounds reconcile_orphaned_dispatch's re-dispatch retries so a
    # permanently-undispatchable job (e.g. the broker is down) reaches
    # a clean terminal FAILED state instead of being retried forever.
    # Starts at 1: UploadPipeline.process's own initial .delay() call
    # already counts as the first attempt.
    dispatch_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    current_step: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    video = relationship(
        "Video",
        back_populates="processing_jobs",
    )

    stages = relationship(
        "ProcessingStage",
        back_populates="processing_job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )