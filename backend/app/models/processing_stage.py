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


class ProcessingStage(Base):
    """
    Per-stage lifecycle row for one ProcessingJob's video pipeline.

    One row per (processing_job_id, stage_name), updated in place
    across retries - not a new row per attempt. This is what makes a
    job resumable: VideoPipelineService.process() checks this row
    before running a stage (COMPLETED -> skip; PENDING/FAILED/stale
    RUNNING -> (re)claim and run) instead of always re-running every
    stage from the top. Column choices deliberately mirror
    ProcessingJob's own (one `finished_at` rather than separate
    completed_at/failed_at; no created_at/updated_at, since
    started_at/finished_at already serve that role).
    """

    __tablename__ = "processing_stages"
    __table_args__ = (
        UniqueConstraint(
            "processing_job_id", "stage_name",
            name="uq_processing_stages_job_id_stage_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    processing_job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "processing_jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    stage_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        nullable=False,
        index=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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

    processing_job = relationship(
        "ProcessingJob",
        back_populates="stages",
    )
