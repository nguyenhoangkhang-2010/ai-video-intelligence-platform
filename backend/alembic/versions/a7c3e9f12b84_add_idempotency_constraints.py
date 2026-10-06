"""add idempotency constraints

Revision ID: a7c3e9f12b84
Revises: f1a2b3c4d5e6
Create Date: 2026-10-07 00:00:00.000000

Phase 2 production-reliability work: makes the video-processing
pipeline's duplicate-prevention guarantees real at the database level
instead of relying only on application-level check-then-insert.

1. uq_processing_jobs_active_per_video - a partial unique index on
   processing_jobs.video_id, scoped to status IN ('PENDING','RUNNING').
   At most one *active* job per video; COMPLETED/FAILED history is
   deliberately excluded from the index so it never blocks a later job.
   The dev and prod databases were checked for existing violations
   before writing this migration - none were found.

2. uq_summaries_video_id_type / uq_translations_video_id_language -
   SummaryService.save_summary / TranslationService.save_translation
   already upsert on these exact keys; these constraints make that
   upsert correct under a genuine concurrent write, not just in the
   common single-writer case. Both dev and prod databases were
   checked for existing duplicate (video_id, type) / (video_id,
   language) rows before writing this migration - none were found.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c3e9f12b84'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'uq_processing_jobs_active_per_video',
        'processing_jobs',
        ['video_id'],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'RUNNING')"),
    )
    op.create_unique_constraint(
        'uq_summaries_video_id_type',
        'summaries',
        ['video_id', 'type'],
    )
    op.create_unique_constraint(
        'uq_translations_video_id_language',
        'translations',
        ['video_id', 'language'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'uq_translations_video_id_language',
        'translations',
        type_='unique',
    )
    op.drop_constraint(
        'uq_summaries_video_id_type',
        'summaries',
        type_='unique',
    )
    op.drop_index(
        'uq_processing_jobs_active_per_video',
        table_name='processing_jobs',
        postgresql_where=sa.text("status IN ('PENDING', 'RUNNING')"),
    )
