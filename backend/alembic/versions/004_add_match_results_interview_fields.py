"""Add interview fields to match_results table

Revision ID: 004
Revises: 003
Create Date: 2024-01-16 12:00:00.000000

This migration adds the missing interview-related columns to match_results table.
Safe to run even if columns already exist (checks before adding).

IMPORTANT: If migration 003 was already applied, you may need to:
1. Run: alembic stamp 003
2. Then run: alembic upgrade head

Or manually add columns using the SQL in MIGRATION_INSTRUCTIONS.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import logging

logger = logging.getLogger(__name__)

# revision identifiers, used by Alembic.
revision = '004'
# Chain from 003 so Alembic has a single head. The migration remains safe because it checks
# for column existence before adding.
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add interview-related columns to match_results table.
    Uses IF NOT EXISTS logic to handle cases where columns might already exist.
    """
    # Check if columns exist before adding them
    conn = op.get_bind()
    
    # Get existing columns
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('match_results')]
    
    # Add interview_enabled if it doesn't exist
    if 'interview_enabled' not in columns:
        op.add_column('match_results', sa.Column('interview_enabled', sa.Boolean(), nullable=False, server_default='false'))
        logger.info("Added interview_enabled column to match_results")
    else:
        logger.info("Column interview_enabled already exists, skipping")
    
    # Add online_interview_enabled if it doesn't exist
    if 'online_interview_enabled' not in columns:
        op.add_column('match_results', sa.Column('online_interview_enabled', sa.Boolean(), nullable=False, server_default='false'))
        logger.info("Added online_interview_enabled column to match_results")
    else:
        logger.info("Column online_interview_enabled already exists, skipping")
    
    # Add shortlisted if it doesn't exist
    if 'shortlisted' not in columns:
        op.add_column('match_results', sa.Column('shortlisted', sa.Boolean(), nullable=False, server_default='false'))
        logger.info("Added shortlisted column to match_results")
    else:
        logger.info("Column shortlisted already exists, skipping")
    
    # Create index for shortlisted if it doesn't exist
    indexes = [idx['name'] for idx in inspector.get_indexes('match_results')]
    if 'ix_match_results_shortlisted' not in indexes:
        op.create_index('ix_match_results_shortlisted', 'match_results', ['shortlisted'])
        logger.info("Created index ix_match_results_shortlisted")
    else:
        logger.info("Index ix_match_results_shortlisted already exists, skipping")


def downgrade() -> None:
    """
    Remove interview-related columns from match_results table.
    """
    # Check if columns exist before removing them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('match_results')]
    indexes = [idx['name'] for idx in inspector.get_indexes('match_results')]
    
    # Drop index if it exists
    if 'ix_match_results_shortlisted' in indexes:
        op.drop_index('ix_match_results_shortlisted', table_name='match_results')
    
    # Drop columns if they exist
    if 'shortlisted' in columns:
        op.drop_column('match_results', 'shortlisted')
    
    if 'online_interview_enabled' in columns:
        op.drop_column('match_results', 'online_interview_enabled')
    
    if 'interview_enabled' in columns:
        op.drop_column('match_results', 'interview_enabled')

