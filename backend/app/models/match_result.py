from sqlalchemy import Column, String, DateTime, ForeignKey, func, Numeric, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False, index=True)
    scores_json = Column(JSONB, nullable=False)  # Overall score, skill match, experience match, etc.
    rank = Column(String(10), nullable=True, index=True)  # Ranking position
    explanation = Column(JSONB, nullable=True)  # AI-generated explanation of match
    overall_score = Column(Numeric(5, 2), nullable=False, index=True)  # 0.00 to 100.00
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Interview-related fields (additive, backward-compatible)
    interview_enabled = Column(Boolean, default=False, nullable=False)  # Toggle to enable interview scheduling
    online_interview_enabled = Column(Boolean, default=False, nullable=False)  # Toggle for online interview
    shortlisted = Column(Boolean, default=False, nullable=False, index=True)  # Whether candidate is shortlisted

    # Relationships
    job = relationship("Job", back_populates="match_results")
    candidate = relationship("Candidate", back_populates="match_results")

    # Composite indexes for efficient queries
    __table_args__ = (
        Index('ix_match_results_job_score', 'job_id', 'overall_score'),
        Index('ix_match_results_job_rank', 'job_id', 'rank'),
    )

    def __repr__(self):
        return f"<MatchResult(id={self.id}, job_id={self.job_id}, candidate_id={self.candidate_id}, score={self.overall_score})>"

