from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum
from app.database import Base


class JobStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements_json = Column(JSONB, nullable=True)  # Skills, experience, education, etc.
    status = Column(Enum(JobStatus), default=JobStatus.DRAFT, nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    creator = relationship("User", backref="jobs")
    processing_queues = relationship("ProcessingQueue", back_populates="job", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.id}, title={self.title}, status={self.status})>"

