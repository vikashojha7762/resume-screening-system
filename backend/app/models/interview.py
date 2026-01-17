"""
Interview Model
Stores interview scheduling and attendance information
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Enum, Integer, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum
from app.database import Base


class InterviewType(str, enum.Enum):
    """Interview type"""
    ONLINE = "online"
    OFFLINE = "offline"


class InterviewStatus(str, enum.Enum):
    """Interview status"""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    IN_PROGRESS = "in_progress"


class Interview(Base):
    """
    Interview scheduling and tracking
    
    Links:
    - job_id: The job position
    - candidate_id: The candidate being interviewed
    - scheduled_by: User who scheduled the interview
    """
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False, index=True)
    
    # Interview scheduling details
    interview_date = Column(DateTime(timezone=True), nullable=False, index=True)
    interview_time = Column(String(10), nullable=False)  # HH:MM format
    interview_timezone = Column(String(50), nullable=False, default="UTC")
    interview_duration = Column(Integer, nullable=False, default=60)  # Duration in minutes
    interviewer_name = Column(String(255), nullable=True)
    interview_type = Column(Enum(InterviewType), default=InterviewType.OFFLINE, nullable=False)
    interview_status = Column(Enum(InterviewStatus), default=InterviewStatus.SCHEDULED, nullable=False, index=True)
    
    # Online interview fields
    online_interview_enabled = Column(Boolean, default=False, nullable=False)
    meeting_link = Column(String(512), nullable=True)  # Secure meeting URL
    meeting_room_id = Column(String(100), nullable=True, unique=True, index=True)  # Unique room identifier
    
    # Attendance tracking
    candidate_joined_at = Column(DateTime(timezone=True), nullable=True)
    interviewer_joined_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    scheduled_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cancellation_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_json = Column(JSONB, nullable=True)  # Additional flexible data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    job = relationship("Job", backref="interviews")
    candidate = relationship("Candidate", backref="interviews")
    scheduler = relationship("User", foreign_keys=[scheduled_by], backref="scheduled_interviews")
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_interview_job_candidate', 'job_id', 'candidate_id'),
        Index('ix_interview_date_status', 'interview_date', 'interview_status'),
    )
    
    def __repr__(self):
        return f"<Interview(id={self.id}, job_id={self.job_id}, candidate_id={self.candidate_id}, status={self.interview_status})>"


class InterviewLog(Base):
    """
    Audit log for interview actions
    Tracks all changes and events related to interviews
    """
    __tablename__ = "interview_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False, index=True)
    
    # Action details
    action = Column(String(50), nullable=False)  # SCHEDULED, RESCHEDULED, CANCELLED, JOINED, COMPLETED, etc.
    action_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # User who performed action
    action_reason = Column(Text, nullable=True)  # Optional reason for action
    
    # Changes tracking
    old_values = Column(JSONB, nullable=True)  # Previous state
    new_values = Column(JSONB, nullable=True)  # New state
    
    # Metadata
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    interview = relationship("Interview", backref="logs")
    user = relationship("User", foreign_keys=[action_by], backref="interview_actions")
    
    def __repr__(self):
        return f"<InterviewLog(id={self.id}, interview_id={self.interview_id}, action={self.action})>"

