"""Add annotation tag and ai_question models

Revision ID: 002_annotations_tags
Revises: 001_initial
Create Date: 2025-10-08 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '002_annotations_tags'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create annotations table
    op.create_table(
        'annotations',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.String(36), nullable=False),
        sa.Column('chunk_id', sa.String(36), nullable=True),
        sa.Column('annotation_type', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('position_x', sa.Float(), nullable=False),
        sa.Column('position_y', sa.Float(), nullable=False),
        sa.Column('position_width', sa.Float(), nullable=False),
        sa.Column('position_height', sa.Float(), nullable=False),
        sa.Column('color', sa.String(7), nullable=False,
                  server_default='#FFFF00'),
        sa.Column('tag_id', sa.String(36), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['chunk_id'], ['chunks.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_annotations_user_document',
                    'annotations', ['user_id', 'document_id'])
    op.create_index('idx_annotations_page', 'annotations',
                    ['document_id', 'page_number'])
    op.create_index('idx_annotations_type', 'annotations', ['annotation_type'])

    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('color', sa.String(7), nullable=False,
                  server_default='#3B82F6'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'name', name='uq_tags_user_name')
    )
    op.create_index('idx_tags_user', 'tags', ['user_id'])

    # Add foreign key to annotations.tag_id after tags table is created
    # SQLite doesn't support adding foreign keys after table creation,
    # so this constraint is already included in the annotations table definition above

    # Create ai_questions table
    op.create_table(
        'ai_questions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.String(36), nullable=False),
        sa.Column('chunk_id', sa.String(36), nullable=True),
        sa.Column('selected_text', sa.Text(), nullable=False),
        sa.Column('context_text', sa.Text(), nullable=True),
        sa.Column('user_question', sa.Text(), nullable=False),
        sa.Column('ai_answer', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('position_x', sa.Float(), nullable=False),
        sa.Column('position_y', sa.Float(), nullable=False),
        sa.Column('model_used', sa.String(100), nullable=False,
                  server_default='gemini-1.5-flash'),
        sa.Column('response_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['chunk_id'], ['chunks.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_ai_questions_user_document',
                    'ai_questions', ['user_id', 'document_id'])
    op.create_index('idx_ai_questions_page', 'ai_questions',
                    ['document_id', 'page_number'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('ai_questions')
    op.drop_table('tags')
    op.drop_table('annotations')
