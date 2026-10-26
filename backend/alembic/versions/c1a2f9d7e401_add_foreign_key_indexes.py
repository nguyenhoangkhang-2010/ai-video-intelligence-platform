"""add foreign key indexes

Revision ID: c1a2f9d7e401
Revises: 98fe6f97d0c4
Create Date: 2026-09-23 00:00:00.000000

Every ownership/"get by video" query in this app filters on a foreign
key column (videos.owner_id, and *.video_id on every child table),
but no migration up to this point ever indexed one - Postgres does
not auto-index foreign keys the way it does primary keys. This adds
one b-tree index per FK column that didn't already have one from a
unique constraint (transcripts.video_id is already unique-indexed via
its own constraint, so it's intentionally skipped here).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c1a2f9d7e401'
down_revision: Union[str, Sequence[str], None] = '98fe6f97d0c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(op.f('ix_videos_owner_id'), 'videos', ['owner_id'])
    op.create_index(op.f('ix_chapters_video_id'), 'chapters', ['video_id'])
    op.create_index(op.f('ix_chat_histories_user_id'), 'chat_histories', ['user_id'])
    op.create_index(op.f('ix_chat_histories_video_id'), 'chat_histories', ['video_id'])
    op.create_index(op.f('ix_embeddings_video_id'), 'embeddings', ['video_id'])
    op.create_index(op.f('ix_flashcards_video_id'), 'flashcards', ['video_id'])
    op.create_index(op.f('ix_processing_jobs_video_id'), 'processing_jobs', ['video_id'])
    op.create_index(op.f('ix_quizzes_video_id'), 'quizzes', ['video_id'])
    op.create_index(op.f('ix_summaries_video_id'), 'summaries', ['video_id'])
    op.create_index(op.f('ix_translations_video_id'), 'translations', ['video_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_translations_video_id'), table_name='translations')
    op.drop_index(op.f('ix_summaries_video_id'), table_name='summaries')
    op.drop_index(op.f('ix_quizzes_video_id'), table_name='quizzes')
    op.drop_index(op.f('ix_processing_jobs_video_id'), table_name='processing_jobs')
    op.drop_index(op.f('ix_flashcards_video_id'), table_name='flashcards')
    op.drop_index(op.f('ix_embeddings_video_id'), table_name='embeddings')
    op.drop_index(op.f('ix_chat_histories_video_id'), table_name='chat_histories')
    op.drop_index(op.f('ix_chat_histories_user_id'), table_name='chat_histories')
    op.drop_index(op.f('ix_chapters_video_id'), table_name='chapters')
    op.drop_index(op.f('ix_videos_owner_id'), table_name='videos')
