"""Initial migration with all tables and pgvector

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create enum types
    job_status_enum = postgresql.ENUM('draft', 'active', 'closed', 'archived', name='jobstatus', create_type=False)
    job_status_enum.create(op.get_bind(), checkfirst=True)
    
    resume_status_enum = postgresql.ENUM('uploaded', 'parsing', 'parsed', 'processing', 'processed', 'error', name='resumestatus', create_type=False)
    resume_status_enum.create(op.get_bind(), checkfirst=True)
    
    processing_status_enum = postgresql.ENUM('pending', 'processing', 'completed', 'failed', 'retrying', name='processingstatus', create_type=False)
    processing_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements_json', postgresql.JSONB(), nullable=True),
        sa.Column('status', job_status_enum, nullable=False, server_default='draft'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    )
    op.create_index('ix_jobs_id', 'jobs', ['id'])
    op.create_index('ix_jobs_title', 'jobs', ['title'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    
    # Create resumes table
    op.create_table(
        'resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('file_path', sa.String(512), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.String(50), nullable=True),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('parsed_data_json', postgresql.JSONB(), nullable=True),
        sa.Column('embedding_vector', Vector(384), nullable=True),
        sa.Column('status', resume_status_enum, nullable=False, server_default='uploaded'),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
    )
    op.create_index('ix_resumes_id', 'resumes', ['id'])
    op.create_index('ix_resumes_status', 'resumes', ['status'])
    # Vector similarity index
    op.execute("CREATE INDEX IF NOT EXISTS ix_resume_embedding ON resumes USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100)")
    
    # Create candidates table
    op.create_table(
        'candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('anonymized_id', sa.String(100), nullable=False, unique=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('masked_data_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
    )
    op.create_index('ix_candidates_id', 'candidates', ['id'])
    op.create_index('ix_candidates_anonymized_id', 'candidates', ['anonymized_id'])
    
    # Create processing_queue table
    op.create_table(
        'processing_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', processing_status_enum, nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.String(10), nullable=False, server_default='0'),
        sa.Column('progress', sa.String(10), nullable=False, server_default='0'),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
    )
    op.create_index('ix_processing_queue_id', 'processing_queue', ['id'])
    op.create_index('ix_processing_queue_job_id', 'processing_queue', ['job_id'])
    op.create_index('ix_processing_queue_resume_id', 'processing_queue', ['resume_id'])
    op.create_index('ix_processing_queue_status', 'processing_queue', ['status'])
    op.create_index('ix_processing_queue_job_status', 'processing_queue', ['job_id', 'status'])
    op.create_index('ix_processing_queue_resume_status', 'processing_queue', ['resume_id', 'status'])
    
    # Create match_results table
    op.create_table(
        'match_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scores_json', postgresql.JSONB(), nullable=False),
        sa.Column('rank', sa.String(10), nullable=True),
        sa.Column('explanation', postgresql.JSONB(), nullable=True),
        sa.Column('overall_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
    )
    op.create_index('ix_match_results_id', 'match_results', ['id'])
    op.create_index('ix_match_results_job_id', 'match_results', ['job_id'])
    op.create_index('ix_match_results_candidate_id', 'match_results', ['candidate_id'])
    op.create_index('ix_match_results_overall_score', 'match_results', ['overall_score'])
    op.create_index('ix_match_results_rank', 'match_results', ['rank'])
    op.create_index('ix_match_results_job_score', 'match_results', ['job_id', 'overall_score'])
    op.create_index('ix_match_results_job_rank', 'match_results', ['job_id', 'rank'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('match_results')
    op.drop_table('processing_queue')
    op.drop_table('candidates')
    op.drop_table('resumes')
    op.drop_table('jobs')
    op.drop_table('users')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS processingstatus')
    op.execute('DROP TYPE IF EXISTS resumestatus')
    op.execute('DROP TYPE IF EXISTS jobstatus')
    
    # Drop pgvector extension (optional, may be used by other tables)
    # op.execute('DROP EXTENSION IF EXISTS vector')

