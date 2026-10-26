"""add heartbeat to processing_jobs

Revision ID: c7e2a9d4f1b3
Revises: b1b84c9c1d78
Create Date: 2026-10-26 00:00:00.000000

A worker that dies mid-pipeline (container restart, Docker engine
crash, OOM kill) used to leave its job RUNNING with nothing able to
tell it apart from a job that is merely slow: the only signal was
started_at, so the stale-RUNNING reclaim had to wait the full
task_time_limit (an hour) and only fired if Celery happened to
redeliver the task. Meanwhile the UI showed "processing" forever and
the Retry button never appeared, since retry only accepts FAILED jobs.

heartbeat_at is refreshed every few seconds by the worker that owns
the job (app.workers.heartbeat.JobHeartbeat). A RUNNING job whose
heartbeat has gone quiet for longer than
CELERY_JOB_HEARTBEAT_TIMEOUT_SECONDS is genuinely orphaned - see
ProcessingJobService.reconcile_stale_running.

Nullable with no backfill: existing rows (all already terminal in
practice) keep NULL, and the reclaim logic falls back to the old
started_at + task_time_limit rule for a RUNNING row with no heartbeat.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7e2a9d4f1b3'
down_revision: Union[str, Sequence[str], None] = 'b1b84c9c1d78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'processing_jobs',
        sa.Column(
            'heartbeat_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('processing_jobs', 'heartbeat_at')
