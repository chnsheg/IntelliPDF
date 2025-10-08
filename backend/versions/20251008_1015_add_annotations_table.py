"""Add annotations table

Revision ID: 20251008_1015_add_annotations_table
Revises: 
Create Date: 2025-10-08 10:15:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251008_1015_add_annotations_table'
down_revision = 'd81956692a85'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('annotations',
                    sa.Column('id', sa.String(length=36), nullable=False,
                              comment='Annotation unique identifier'),
                    sa.Column('document_id', sa.String(length=36),
                              nullable=False, comment='Document ID'),
                    sa.Column('user_id', sa.String(length=36),
                              nullable=False, comment='Owner user ID'),
                    sa.Column('annotation_type', sa.String(length=32),
                              nullable=False, comment='Type of annotation'),
                    sa.Column('page_number', sa.Integer(), nullable=True,
                              comment='Page number where annotation is located'),
                    sa.Column('position', sa.JSON(), nullable=True,
                              comment='Bounding box or position data'),
                    sa.Column('color', sa.String(length=20), nullable=True,
                              comment='Color used for highlight/tag'),
                    sa.Column('content', sa.Text(), nullable=True,
                              comment='User note or tagged text'),
                    sa.Column('tags', sa.JSON(), nullable=False,
                              comment='User provided tags'),
                    sa.Column('metadata', sa.JSON(), nullable=False,
                              comment='Additional annotation metadata'),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
                    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index('idx_annotations_document_created', 'annotations', [
                    'document_id', 'created_at'], unique=False)


def downgrade():
    op.drop_index('idx_annotations_document_created', table_name='annotations')
    op.drop_table('annotations'
                  )
