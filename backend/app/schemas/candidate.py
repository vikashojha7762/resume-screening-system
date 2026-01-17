from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any


class CandidateBase(BaseModel):
    anonymized_id: str


class CandidateCreate(CandidateBase):
    resume_id: UUID
    masked_data_json: Optional[Dict[str, Any]] = None


class CandidateInDB(CandidateBase):
    id: UUID
    resume_id: UUID
    masked_data_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Candidate(CandidateInDB):
    pass

