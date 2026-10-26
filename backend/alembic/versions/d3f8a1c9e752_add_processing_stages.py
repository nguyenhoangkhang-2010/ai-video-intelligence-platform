"""add processing_stages table

Revision ID: d3f8a1c9e752
Revises: a7c3e9f12b84
Create Date: 2026-10-07 00:00:00.000000

Phase B production-reliability work: makes the video-processing
pipeline resumable by giving each of its 8 stages (metadata,
transcription, summary, embedding, translation, quiz, chapter,
flashcard) its own persisted lifecycle row per ProcessingJob, instead
of the job having a single all-or-nothing status. One row per
(processing_job_id, stage_name), updated in place across retries -
not a new row per attempt (see ProcessingStage's own docstring).

This is purely additive (a new table, FK CASCADE to an existing one) -
no existing table/column changes, no backfill needed. Historical
COMPLETED jobs simply have zero stage rows, which is expected and
never an error; stage rows are forward-looking bookkeeping only for
in-flight/future jobs.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3f8a1c9e752'
down_revision: Union[str, Sequence[str], None] = 'a7c3e9f12b84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'processing_stages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('processing_job_id', sa.Integer(), nullable=False),
        sa.Column('stage_name', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ['processing_job_id'], ['processing_jobs.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'processing_job_id', 'stage_name',
            name='uq_processing_stages_job_id_stage_name',
        ),
    )
    op.create_index(
        op.f('ix_processing_stages_id'),
        'processing_stages', ['id'],
    )
    op.create_index(
        op.f('ix_processing_stages_processing_job_id'),
        'processing_stages', ['processing_job_id'],
    )
    op.create_index(
        op.f('ix_processing_stages_status'),
        'processing_stages', ['status'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_processing_stages_status'),
        table_name='processing_stages',
    )
    op.drop_index(
        op.f('ix_processing_stages_processing_job_id'),
        table_name='processing_stages',
    )
    op.drop_index(
        op.f('ix_processing_stages_id'),
        table_name='processing_stages',
    )
    op.drop_table('processing_stages')
