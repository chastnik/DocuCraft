"""Add AI configuration table

Revision ID: 003_add_ai_config
Revises: 002_add_git_config
Create Date: 2024-01-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_ai_config'
down_revision = '002_add_git_config'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ai_configurations table
    op.create_table(
        'ai_configurations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('api_key', sa.Text(), nullable=False),
        sa.Column('config', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique index on provider
    op.create_index('ix_ai_configurations_provider', 'ai_configurations', ['provider'], unique=True)


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_ai_configurations_provider', table_name='ai_configurations')
    
    # Drop table
    op.drop_table('ai_configurations')

