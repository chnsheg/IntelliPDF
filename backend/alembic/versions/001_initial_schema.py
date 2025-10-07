"""Initial database schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-10-07 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('processing_started_at', sa.DateTime(), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('chunk_count', sa.Integer(),
                  nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_path'),
        sa.UniqueConstraint('content_hash')
    )
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_content_hash', 'documents', ['content_hash'])

    # Create chunks table
    op.create_table(
        'chunks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.String(36), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_type', sa.String(20), nullable=False),
        sa.Column('start_page', sa.Integer(), nullable=False),
        sa.Column('end_page', sa.Integer(), nullable=False),
        sa.Column('token_count', sa.Integer(),
                  nullable=False, server_default='0'),
        sa.Column('vector_id', sa.String(100), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['document_id'], ['documents.id'], ondelete='CASCADE')
    )
    op.create_index('ix_chunks_document_id', 'chunks', ['document_id'])
    op.create_index('ix_chunks_chunk_type', 'chunks', ['chunk_type'])
    op.create_index('ix_chunks_vector_id', 'chunks', ['vector_id'])


def downgrade() -> None:
    op.drop_table('chunks')
    op.drop_table('documents')
