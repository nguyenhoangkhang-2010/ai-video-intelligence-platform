"""add visual segments and content source

Revision ID: e6a1c3f9b7d2
Revises: d4b8e1f6a2c9
Create Date: 2026-10-26 12:00:00.000000

Visual understanding (ai.vision): keyframes are read by a vision
model for on-screen text and a description of the picture.

- visual_segments: one row per span of video showing the same thing,
  with its keyframe, on-screen text, description and how related it
  is to what was being said (speech_similarity).
- transcripts.source: "speech", or "visual" for a video with no
  speech whose transcript was built from what is on screen (such
  videos used to fail processing outright).
- embeddings.source: whether a retrieval chunk was said or shown, so
  search results and chat citations can say which.

Existing rows default to "speech", which is what they all are.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6a1c3f9b7d2'
down_revision: Union[str, Sequence[str], None] = 'd4b8e1f6a2c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'visual_segments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('frame_key', sa.String(length=255), nullable=True),
        sa.Column('on_screen_text', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('speech_similarity', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_visual_segments_id'), 'visual_segments', ['id'], unique=False)
    op.create_index(op.f('ix_visual_segments_video_id'), 'visual_segments', ['video_id'], unique=False)
    op.add_column(
        'transcripts',
        sa.Column('source', sa.String(length=20), nullable=False, server_default='speech'),
    )
    op.add_column(
        'embeddings',
        sa.Column('source', sa.String(length=20), nullable=False, server_default='speech'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('embeddings', 'source')
    op.drop_column('transcripts', 'source')
    op.drop_index(op.f('ix_visual_segments_video_id'), table_name='visual_segments')
    op.drop_index(op.f('ix_visual_segments_id'), table_name='visual_segments')
    op.drop_table('visual_segments')
