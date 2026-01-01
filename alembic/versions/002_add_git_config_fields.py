"""Add Git configuration fields to projects

Revision ID: 002_add_git_config
Revises: 001_initial
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_git_config'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create GitProvider enum type
    git_provider_enum = postgresql.ENUM('github', 'gitlab', 'gitea', 'custom', name='gitprovider', create_type=True)
    git_provider_enum.create(op.get_bind(), checkfirst=True)

    # Add new Git configuration columns to projects table
    op.add_column('projects', sa.Column('git_provider', git_provider_enum, nullable=True))
    op.add_column('projects', sa.Column('git_repo_url', sa.String(length=500), nullable=True))
    op.add_column('projects', sa.Column('git_api_base_url', sa.String(length=500), nullable=True))
    op.add_column('projects', sa.Column('git_access_token', sa.Text(), nullable=True))
    op.add_column('projects', sa.Column('git_webhook_secret', sa.String(length=255), nullable=True))

    # Migrate data from legacy fields if they exist
    # This allows backward compatibility
    op.execute("""
        UPDATE projects 
        SET git_provider = 'github'::gitprovider,
            git_repo_url = github_repo_url,
            git_webhook_secret = github_webhook_secret
        WHERE github_repo_url IS NOT NULL 
        AND (git_repo_url IS NULL OR git_repo_url = '')
    """)


def downgrade() -> None:
    # Remove new columns
    op.drop_column('projects', 'git_webhook_secret')
    op.drop_column('projects', 'git_access_token')
    op.drop_column('projects', 'git_api_base_url')
    op.drop_column('projects', 'git_repo_url')
    op.drop_column('projects', 'git_provider')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS gitprovider")

