"""
Interview Schemas
Pydantic models for interview API requests and responses
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.interview import InterviewType, InterviewStatus


class InterviewBase(BaseModel):
    """Base interview schema"""
    interview_date: datetime = Field(..., description="Interview date and time")
    interview_time: str = Field(..., pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', description="Interview time in HH:MM format")
    interview_timezone: str = Field(default="UTC", description="Timezone (e.g., UTC, America/New_York)")
    interview_duration: int = Field(default=60, ge=15, le=480, description="Duration in minutes (15-480)")
    interviewer_name: Optional[str] = Field(None, max_length=255, description="Name of interviewer")
    interview_type: InterviewType = Field(default=InterviewType.OFFLINE, description="ONLINE or OFFLINE")
    online_interview_enabled: bool = Field(default=False, description="Enable online interview")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('interview_date')
    @classmethod
    def validate_future_date(cls, v: datetime) -> datetime:
        """Ensure interview is scheduled in the future"""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if v.replace(tzinfo=timezone.utc) < now:
            raise ValueError("Interview date must be in the future")
        return v


class InterviewCreate(InterviewBase):
    """Schema for creating a new interview"""
    job_id: UUID = Field(..., description="Job ID")
    candidate_id: UUID = Field(..., description="Candidate ID")


class InterviewUpdate(BaseModel):
    """Schema for updating an interview"""
    interview_date: Optional[datetime] = None
    interview_time: Optional[str] = Field(None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    interview_timezone: Optional[str] = None
    interview_duration: Optional[int] = Field(None, ge=15, le=480)
    interviewer_name: Optional[str] = None
    interview_type: Optional[InterviewType] = None
    online_interview_enabled: Optional[bool] = None
    interview_status: Optional[InterviewStatus] = None
    cancellation_reason: Optional[str] = None
    notes: Optional[str] = None


class InterviewInDB(InterviewBase):
    """Interview database model schema"""
    id: UUID
    job_id: UUID
    candidate_id: UUID
    interview_status: InterviewStatus
    meeting_link: Optional[str] = None
    meeting_room_id: Optional[str] = None
    candidate_joined_at: Optional[datetime] = None
    interviewer_joined_at: Optional[datetime] = None
    scheduled_by: UUID
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Interview(InterviewInDB):
    """Public interview schema"""
    pass


class InterviewListResponse(BaseModel):
    """Response for listing interviews"""
    items: list[Interview]
    total: int
    page: int
    page_size: int


class InterviewJoinRequest(BaseModel):
    """Request to join an interview"""
    meeting_room_id: str = Field(..., description="Meeting room ID")
    participant_type: str = Field(..., pattern="^(candidate|interviewer)$", description="Type of participant")


class InterviewJoinResponse(BaseModel):
    """Response for joining an interview"""
    meeting_link: str
    meeting_room_id: str
    interview_id: UUID
    interview_start_time: datetime
    interview_end_time: datetime
    can_join: bool
    message: Optional[str] = None


class InterviewToggleRequest(BaseModel):
    """Request to toggle interview enabled status"""
    interview_enabled: bool = Field(..., description="Enable or disable interview")
    online_interview_enabled: Optional[bool] = Field(None, description="Enable or disable online interview")


class InterviewLogResponse(BaseModel):
    """Response for interview log entry"""
    id: UUID
    interview_id: UUID
    action: str
    action_by: Optional[UUID] = None
    action_reason: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

