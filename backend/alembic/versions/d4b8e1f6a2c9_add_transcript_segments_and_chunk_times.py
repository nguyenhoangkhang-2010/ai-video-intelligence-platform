"""add transcript segments and embedding chunk times

Revision ID: d4b8e1f6a2c9
Revises: c7e2a9d4f1b3
Create Date: 2026-10-26 00:00:00.000000

Whisper already produces timed segments (start/end/text), but only
the joined text was ever stored - every timestamp was thrown away at
the transcription stage. That made a click-to-seek transcript
impossible, left search results and AI-chat citations unable to say
*where* in the video they came from, and forced chapter detection to
re-run Whisper whenever its stage resumed after the transcription
stage had already completed.

- transcripts.segments: the timed segments, as JSON
  ([{"start", "end", "text", "speaker"?}, ...]).
- embeddings.start_time / end_time: the span of video each retrieval
  chunk covers, derived from those segments.

All nullable with no backfill: videos processed before this keep
working exactly as before (plain transcript, citations without a
timestamp) until they are reprocessed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4b8e1f6a2c9'
down_revision: Union[str, Sequence[str], None] = 'c7e2a9d4f1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'transcripts',
        sa.Column('segments', sa.JSON(), nullable=True),
    )
    op.add_column(
        'embeddings',
        sa.Column('start_time', sa.Float(), nullable=True),
    )
    op.add_column(
        'embeddings',
        sa.Column('end_time', sa.Float(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('embeddings', 'end_time')
    op.drop_column('embeddings', 'start_time')
    op.drop_column('transcripts', 'segments')
