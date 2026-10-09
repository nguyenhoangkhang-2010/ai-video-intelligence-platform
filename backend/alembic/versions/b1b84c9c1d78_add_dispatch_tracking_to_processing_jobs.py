"""add dispatch tracking to processing_jobs

Revision ID: b1b84c9c1d78
Revises: d3f8a1c9e752
Create Date: 2026-10-09 00:00:00.000000

Closes the dual-write gap between committing a ProcessingJob row and
dispatching its Celery task (UploadPipeline.process): if the
dispatch call never happens or never arrives (process crash, broker
unreachable), the job was previously stuck PENDING forever with
nothing able to tell it apart from a job whose dispatch is merely a
few seconds in flight - there was no timestamp on this table at all.

created_at makes that distinguishable (a PENDING job with no
started_at is "orphaned" once it is older than the dispatch grace
period, not before). dispatch_attempts bounds the reconciliation
mechanism's re-dispatch retries so a permanently-undispatchable job
(e.g. the broker is down) reaches a clean terminal FAILED state
instead of being retried forever.

Backfills existing rows via server_default at ALTER TABLE time
(CURRENT_TIMESTAMP/1) so this is purely additive - no existing rows
become unreadable, and historical jobs (including the two known
orphaned PENDING rows, left untouched by this migration) simply get
today's timestamp as a reasonable "we don't know, treat as old
enough to reconcile on next read" default.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1b84c9c1d78'
down_revision: Union[str, Sequence[str], None] = 'd3f8a1c9e752'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'processing_jobs',
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
    )
    op.add_column(
        'processing_jobs',
        sa.Column(
            'dispatch_attempts',
            sa.Integer(),
            nullable=False,
            server_default='1',
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('processing_jobs', 'dispatch_attempts')
    op.drop_column('processing_jobs', 'created_at')
