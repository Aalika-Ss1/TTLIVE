"""add ocr tables

Revision ID: 975e22a9d66d
Revises: 82b6e3d859e6
Create Date: 2026-06-16 19:39:07.887724
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '975e22a9d66d'
down_revision: str | None = '82b6e3d859e6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create attachments table
    op.create_table(
        'attachments',
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attachments_checksum'), 'attachments', ['checksum'], unique=True)

    # Create ocr_suggestions table
    op.create_table(
        'ocr_suggestions',
        sa.Column('attachment_id', sa.String(length=36), nullable=False),
        sa.Column('score_id', sa.String(length=36), nullable=True),
        sa.Column('player_name_raw', sa.String(length=120), nullable=True),
        sa.Column('detected_placement', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('raw_ocr_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.id'], ),
        sa.ForeignKeyConstraint(['score_id'], ['scores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ocr_suggestions_attachment_id'), 'ocr_suggestions', ['attachment_id'], unique=False)
    op.create_index(op.f('ix_ocr_suggestions_score_id'), 'ocr_suggestions', ['score_id'], unique=False)
    op.create_index(op.f('ix_ocr_suggestions_status'), 'ocr_suggestions', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ocr_suggestions_status'), table_name='ocr_suggestions')
    op.drop_index(op.f('ix_ocr_suggestions_score_id'), table_name='ocr_suggestions')
    op.drop_index(op.f('ix_ocr_suggestions_attachment_id'), table_name='ocr_suggestions')
    op.drop_table('ocr_suggestions')
    op.drop_index(op.f('ix_attachments_checksum'), table_name='attachments')
    op.drop_table('attachments')
