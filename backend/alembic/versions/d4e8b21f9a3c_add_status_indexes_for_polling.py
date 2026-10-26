"""add status indexes for polling queries

Revision ID: d4e8b21f9a3c
Revises: c1a2f9d7e401
Create Date: 2026-09-25 00:00:00.000000

videos.status and processing_jobs.status are both queried repeatedly
on the hot path (video-list-by-status, job PENDING->RUNNING claim
during processing, and every frontend polling request via
GET /videos/{id}/status) but neither had an index - the previous
migration (c1a2f9d7e401) indexed every foreign key but not these two
status columns.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd4e8b21f9a3c'
down_revision: Union[str, Sequence[str], None] = 'c1a2f9d7e401'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(op.f('ix_videos_status'), 'videos', ['status'])
    op.create_index(op.f('ix_processing_jobs_status'), 'processing_jobs', ['status'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_processing_jobs_status'), table_name='processing_jobs')
    op.drop_index(op.f('ix_videos_status'), table_name='videos')
