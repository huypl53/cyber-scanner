"""add model profile fields to ml_models table

Revision ID: 20251130_133448
Revises: b725fdb4d6cd
Create Date: 2025-11-30 13:34:48

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251130_133448'
down_revision = 'b725fdb4d6cd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add model profile columns to ml_models table
    op.add_column('ml_models', sa.Column('expected_features', sa.JSON(), nullable=True))
    op.add_column('ml_models', sa.Column('class_labels', sa.JSON(), nullable=True))
    op.add_column('ml_models', sa.Column('preprocessing_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove model profile columns from ml_models table
    op.drop_column('ml_models', 'preprocessing_notes')
    op.drop_column('ml_models', 'class_labels')
    op.drop_column('ml_models', 'expected_features')
