"""
Match results endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional, Dict
from uuid import UUID
from decimal import Decimal
from app.database import get_db
from app.models.match_result import MatchResult
from app.models.user import User
from app.schemas.match_result import (
    MatchResult as MatchResultSchema,
    MatchResultListResponse,
    MatchResultFilter
)
from app.core.dependencies import get_current_active_user
from app.services.matching_orchestrator import matching_orchestrator
from app.services.audit_logger import audit_logger
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/results", tags=["results"])


class MatchRequest(BaseModel):
    candidate_ids: Optional[List[UUID]] = None
    strategy: str = Field("standard", pattern="^(standard|fast|comprehensive)$")
    weights: Optional[Dict[str, float]] = None
    diversity_weight: float = Field(0.0, ge=0.0, le=1.0)
    enable_bias_detection: bool = True


@router.get("", response_model=MatchResultListResponse)
async def list_results(
    job_id: Optional[UUID] = Query(None, alias="job_id"),
    min_score: Optional[Decimal] = Query(None, ge=0, le=100),
    max_score: Optional[Decimal] = Query(None, ge=0, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get ranked match results with filtering
    """
    query = db.query(MatchResult)
    
    # Filter by job_id
    if job_id:
        query = query.filter(MatchResult.job_id == job_id)
    
    # Filter by score range
    if min_score is not None:
        query = query.filter(MatchResult.overall_score >= min_score)
    if max_score is not None:
        query = query.filter(MatchResult.overall_score <= max_score)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering by score (descending)
    results = query.order_by(desc(MatchResult.overall_score)).offset((page - 1) * page_size).limit(page_size).all()
    
    return MatchResultListResponse(
        items=results,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{result_id}", response_model=MatchResultSchema)
async def get_result(
    result_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific match result by ID
    """
    result = db.query(MatchResult).filter(MatchResult.id == result_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match result not found"
        )
    
    return result


@router.get("/job/{job_id}/ranked", response_model=MatchResultListResponse)
async def get_ranked_results_for_job(
    job_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    min_score: Optional[Decimal] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get ranked candidates for a specific job
    """
    query = db.query(MatchResult).filter(MatchResult.job_id == job_id)
    
    # Filter by minimum score if provided
    if min_score is not None:
        query = query.filter(MatchResult.overall_score >= min_score)
    
    # Get results ordered by score (descending) and rank
    results = query.order_by(
        desc(MatchResult.overall_score),
        MatchResult.rank.asc()
    ).limit(limit).all()
    
    # Update ranks if needed
    for idx, result in enumerate(results, start=1):
        if result.rank != str(idx):
            result.rank = str(idx)
    
    db.commit()
    
    return MatchResultListResponse(
        items=results,
        total=len(results),
        page=1,
        page_size=limit
    )


@router.post("/job/{job_id}/match")
async def match_job_to_candidates(
    job_id: UUID,
    match_request: MatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Match a job to candidates using the matching orchestrator
    """
    try:
        # Log matching initiation
        audit_logger.log_matching_event(
            'match_initiated',
            str(job_id),
            user_id=str(current_user.id),
            details={
                'strategy': match_request.strategy,
                'diversity_weight': match_request.diversity_weight,
                'candidate_count': len(match_request.candidate_ids) if match_request.candidate_ids else 'all'
            }
        )
        
        # Convert candidate IDs to strings if provided
        candidate_ids = [str(cid) for cid in match_request.candidate_ids] if match_request.candidate_ids else None
        
        # Execute matching
        results = matching_orchestrator.match_job_to_candidates(
            job_id=str(job_id),
            candidate_ids=candidate_ids,
            strategy=match_request.strategy,
            weights=match_request.weights,
            diversity_weight=match_request.diversity_weight,
            enable_bias_detection=match_request.enable_bias_detection
        )
        
        if 'error' in results:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=results['error']
            )
        
        return results
        
    except Exception as e:
        logger.error(f"Error matching job to candidates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during matching: {str(e)}"
        )

