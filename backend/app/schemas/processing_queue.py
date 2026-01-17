from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models.processing_queue import ProcessingStatus


class ProcessingQueueBase(BaseModel):
    job_id: UUID
    resume_id: UUID


class ProcessingQueueCreate(ProcessingQueueBase):
    metadata_json: Optional[Dict[str, Any]] = None


class ProcessingQueueUpdate(BaseModel):
    status: Optional[ProcessingStatus] = None
    error_message: Optional[str] = None
    retry_count: Optional[str] = None
    progress: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class ProcessingQueueInDB(ProcessingQueueBase):
    id: UUID
    status: ProcessingStatus
    error_message: Optional[str] = None
    retry_count: str
    progress: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProcessingQueue(ProcessingQueueInDB):
    pass


class ProcessingQueueListResponse(BaseModel):
    items: List[ProcessingQueue]
    total: int
    page: int
    page_size: int

