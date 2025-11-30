"""add ml_models table for model versioning

Revision ID: b725fdb4d6cd
Revises: 20251128_004833
Create Date: 2025-11-28 22:54:12.264277

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b725fdb4d6cd'
down_revision = '20251128_004833'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ml_models table for tracking model versions
    op.create_table(
        'ml_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('version', sa.String(length=100), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_format', sa.String(length=20), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('model_metadata', sa.JSON(), nullable=True),
        sa.Column('validation_results', sa.JSON(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('uploaded_by', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_ml_models_id'), 'ml_models', ['id'], unique=False)
    op.create_index(op.f('ix_ml_models_model_type'), 'ml_models', ['model_type'], unique=False)
    op.create_index(op.f('ix_ml_models_version'), 'ml_models', ['version'], unique=False)
    op.create_index(op.f('ix_ml_models_is_active'), 'ml_models', ['is_active'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_ml_models_is_active'), table_name='ml_models')
    op.drop_index(op.f('ix_ml_models_version'), table_name='ml_models')
    op.drop_index(op.f('ix_ml_models_model_type'), table_name='ml_models')
    op.drop_index(op.f('ix_ml_models_id'), table_name='ml_models')

    # Drop table
    op.drop_table('ml_models')
