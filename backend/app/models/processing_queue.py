from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Enum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum
from app.database import Base


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ProcessingQueue(Base):
    __tablename__ = "processing_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, index=True)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(String(10), default="0", nullable=False)
    progress = Column(String(10), default="0", nullable=False)  # 0-100
    metadata_json = Column(JSONB, nullable=True)  # Additional processing metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    job = relationship("Job", back_populates="processing_queues")
    resume = relationship("Resume", back_populates="processing_queues")

    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_processing_queue_job_status', 'job_id', 'status'),
        Index('ix_processing_queue_resume_status', 'resume_id', 'status'),
    )

    def __repr__(self):
        return f"<ProcessingQueue(id={self.id}, job_id={self.job_id}, resume_id={self.resume_id}, status={self.status})>"

