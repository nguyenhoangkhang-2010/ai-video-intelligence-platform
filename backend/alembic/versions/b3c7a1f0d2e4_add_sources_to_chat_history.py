"""add sources to chat history

Revision ID: b3c7a1f0d2e4
Revises: d4e8b21f9a3c
Create Date: 2026-09-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c7a1f0d2e4'
down_revision: Union[str, Sequence[str], None] = 'd4e8b21f9a3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('chat_histories', sa.Column('sources', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('chat_histories', 'sources')
