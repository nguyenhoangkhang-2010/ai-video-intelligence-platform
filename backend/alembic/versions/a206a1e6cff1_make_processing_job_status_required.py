"""make processing job status required

Revision ID: a206a1e6cff1
Revises: 7237d7da3655
Create Date: 2026-07-26 17:08:22.816270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a206a1e6cff1'
down_revision: Union[str, Sequence[str], None] = '7237d7da3655'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Intentional no-op, not an unfinished migration: `processing_jobs.
    status` was already created `nullable=False` in its originating
    migration (4d0af1434cf0), so there was no actual column-level
    change to generate here. Autogenerate created this revision purely
    to record the model-level intent in the migration history timeline
    - safe to leave as a genuine pass, and left as such rather than
    removed, since it has already run against real databases and
    revision history is never rewritten after the fact.
    """
    pass


def downgrade() -> None:
    """No-op for the same reason as upgrade() - see that docstring."""
    pass
