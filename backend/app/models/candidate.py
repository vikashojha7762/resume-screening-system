from sqlalchemy import Column, String, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    anonymized_id = Column(String(100), unique=True, index=True, nullable=False)  # For privacy
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, unique=True)
    masked_data_json = Column(JSONB, nullable=True)  # Anonymized personal information
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    resume = relationship("Resume", back_populates="candidates")
    match_results = relationship("MatchResult", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Candidate(id={self.id}, anonymized_id={self.anonymized_id})>"

