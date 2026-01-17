from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models.job import JobStatus


class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    requirements_json: Optional[Dict[str, Any]] = None


class JobCreate(JobBase):
    status: Optional[JobStatus] = JobStatus.DRAFT


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    requirements_json: Optional[Dict[str, Any]] = None
    status: Optional[JobStatus] = None


class JobInDB(JobBase):
    id: UUID
    status: JobStatus
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Job(JobInDB):
    pass


class JobListResponse(BaseModel):
    items: List[Job]
    total: int
    page: int
    page_size: int

