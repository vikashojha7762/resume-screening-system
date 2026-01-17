"""Add interview scheduling system

Revision ID: 003
Revises: 002_seed_admin_user
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002_seed_admin'  # Matches revision ID from 002_seed_admin_user.py
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add interview-related fields to match_results table (additive, backward-compatible)
    op.add_column('match_results', sa.Column('interview_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('match_results', sa.Column('online_interview_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('match_results', sa.Column('shortlisted', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('ix_match_results_shortlisted', 'match_results', ['shortlisted'])
    
    # Create enum types safely (avoid DuplicateObject if types already exist)
    interview_type_enum = postgresql.ENUM('online', 'offline', name='interviewtype', create_type=False)
    interview_status_enum = postgresql.ENUM(
        'scheduled', 'completed', 'cancelled', 'no_show', 'in_progress',
        name='interviewstatus',
        create_type=False
    )
    bind = op.get_bind()
    interview_type_enum.create(bind, checkfirst=True)
    interview_status_enum.create(bind, checkfirst=True)

    # Create interviews table
    op.create_table(
        'interviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interview_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('interview_time', sa.String(10), nullable=False),
        sa.Column('interview_timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('interview_duration', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('interviewer_name', sa.String(255), nullable=True),
        sa.Column('interview_type', interview_type_enum, nullable=False, server_default='offline'),
        sa.Column('interview_status', interview_status_enum, nullable=False, server_default='scheduled'),
        sa.Column('online_interview_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('meeting_link', sa.String(512), nullable=True),
        sa.Column('meeting_room_id', sa.String(100), nullable=True, unique=True),
        sa.Column('candidate_joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('interviewer_joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
        sa.ForeignKeyConstraint(['scheduled_by'], ['users.id'], ),
    )
    op.create_index('ix_interviews_id', 'interviews', ['id'])
    op.create_index('ix_interviews_job_id', 'interviews', ['job_id'])
    op.create_index('ix_interviews_candidate_id', 'interviews', ['candidate_id'])
    op.create_index('ix_interviews_interview_date', 'interviews', ['interview_date'])
    op.create_index('ix_interviews_interview_status', 'interviews', ['interview_status'])
    op.create_index('ix_interviews_meeting_room_id', 'interviews', ['meeting_room_id'])
    op.create_index('ix_interview_job_candidate', 'interviews', ['job_id', 'candidate_id'])
    op.create_index('ix_interview_date_status', 'interviews', ['interview_date', 'interview_status'])
    
    # Create interview_logs table
    op.create_table(
        'interview_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('interview_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('action_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_reason', sa.Text(), nullable=True),
        sa.Column('old_values', postgresql.JSONB(), nullable=True),
        sa.Column('new_values', postgresql.JSONB(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ),
        sa.ForeignKeyConstraint(['action_by'], ['users.id'], ),
    )
    op.create_index('ix_interview_logs_id', 'interview_logs', ['id'])
    op.create_index('ix_interview_logs_interview_id', 'interview_logs', ['interview_id'])


def downgrade() -> None:
    # Drop interview_logs table
    op.drop_index('ix_interview_logs_interview_id', table_name='interview_logs')
    op.drop_index('ix_interview_logs_id', table_name='interview_logs')
    op.drop_table('interview_logs')
    
    # Drop interviews table
    op.drop_index('ix_interview_date_status', table_name='interviews')
    op.drop_index('ix_interview_job_candidate', table_name='interviews')
    op.drop_index('ix_interviews_meeting_room_id', table_name='interviews')
    op.drop_index('ix_interviews_interview_status', table_name='interviews')
    op.drop_index('ix_interviews_interview_date', table_name='interviews')
    op.drop_index('ix_interviews_candidate_id', table_name='interviews')
    op.drop_index('ix_interviews_job_id', table_name='interviews')
    op.drop_index('ix_interviews_id', table_name='interviews')
    op.drop_table('interviews')
    
    # Drop enum types
    interview_status_enum = postgresql.ENUM(
        'scheduled', 'completed', 'cancelled', 'no_show', 'in_progress',
        name='interviewstatus',
        create_type=False
    )
    interview_type_enum = postgresql.ENUM('online', 'offline', name='interviewtype', create_type=False)
    bind = op.get_bind()
    interview_status_enum.drop(bind, checkfirst=True)
    interview_type_enum.drop(bind, checkfirst=True)
    
    # Remove columns from match_results
    op.drop_index('ix_match_results_shortlisted', table_name='match_results')
    op.drop_column('match_results', 'shortlisted')
    op.drop_column('match_results', 'online_interview_enabled')
    op.drop_column('match_results', 'interview_enabled')

