from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models.resume import ResumeStatus


class ResumeBase(BaseModel):
    file_name: str
    file_type: str


class ResumeCreate(ResumeBase):
    file_path: str
    file_size: Optional[str] = None


class ResumeUpdate(BaseModel):
    parsed_data_json: Optional[Dict[str, Any]] = None
    status: Optional[ResumeStatus] = None
    embedding_vector: Optional[List[float]] = None  # Will be converted to vector


class ResumeInDB(ResumeBase):
    id: UUID
    file_path: str
    file_size: Optional[str] = None
    parsed_data_json: Optional[Dict[str, Any]] = None
    status: ResumeStatus
    uploaded_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Resume(ResumeInDB):
    pass


class ResumeListResponse(BaseModel):
    items: List[Resume]
    total: int
    page: int
    page_size: int


class ResumeUploadResponse(BaseModel):
    id: UUID
    file_name: str
    status: ResumeStatus
    message: str

