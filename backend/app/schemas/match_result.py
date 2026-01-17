from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal


class MatchResultBase(BaseModel):
    job_id: UUID
    candidate_id: UUID
    scores_json: Dict[str, Any]
    overall_score: Decimal = Field(..., ge=0, le=100)
    rank: Optional[str] = None
    explanation: Optional[Dict[str, Any]] = None


class MatchResultCreate(MatchResultBase):
    pass


class MatchResultUpdate(BaseModel):
    scores_json: Optional[Dict[str, Any]] = None
    overall_score: Optional[Decimal] = Field(None, ge=0, le=100)
    rank: Optional[str] = None
    explanation: Optional[Dict[str, Any]] = None


class MatchResultInDB(MatchResultBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchResult(MatchResultInDB):
    pass


class MatchResultListResponse(BaseModel):
    items: List[MatchResult]
    total: int
    page: int
    page_size: int


class MatchResultFilter(BaseModel):
    job_id: Optional[UUID] = None
    min_score: Optional[Decimal] = Field(None, ge=0, le=100)
    max_score: Optional[Decimal] = Field(None, ge=0, le=100)
    limit: Optional[int] = Field(10, ge=1, le=100)
    offset: Optional[int] = Field(0, ge=0)

