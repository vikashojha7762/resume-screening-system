"""
Candidate Management Endpoints
Handles candidate shortlisting and interview toggle
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from app.database import get_db
from app.models.match_result import MatchResult
from app.models.user import User
from app.schemas.interview import InterviewToggleRequest
from app.core.dependencies import get_current_active_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("/{candidate_id}/shortlist", status_code=status.HTTP_200_OK)
async def shortlist_candidate(
    candidate_id: UUID,
    job_id: UUID = Query(..., description="Job ID"),
    shortlisted: bool = Query(True, description="Shortlist status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Shortlist or unshortlist a candidate for a job
    
    When shortlisted:
    - Candidate becomes eligible for interview scheduling
    - Interview toggle becomes visible
    
    This endpoint uses UPSERT logic - creates a match_result if it doesn't exist.
    """
    try:
        logger.info(f"{'Shortlisting' if shortlisted else 'Unshortlisting'} candidate {candidate_id} for job {job_id} by user {current_user.email}")
        
        # Query for existing match result
        match_result = db.query(MatchResult).filter(
            MatchResult.job_id == job_id,
            MatchResult.candidate_id == candidate_id
        ).first()
        
        # If match_result doesn't exist, create it
        if not match_result:
            logger.info(f"Match result not found for candidate {candidate_id} and job {job_id}. Creating new match_result.")
            try:
                match_result = MatchResult(
                    job_id=job_id,
                    candidate_id=candidate_id,
                    shortlisted=shortlisted,
                    interview_enabled=False,
                    online_interview_enabled=False,
                    scores_json={},  # Empty dict for scores
                    overall_score=Decimal('0.00'),  # Default score
                    rank=None  # No rank initially
                )
                db.add(match_result)
            except Exception as create_error:
                db.rollback()
                error_msg = str(create_error)
                logger.error(f"Error creating match_result: {error_msg}", exc_info=True)
                # Check if it's a column missing error
                if 'column' in error_msg.lower() and ('interview_enabled' in error_msg or 'shortlisted' in error_msg):
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Database schema mismatch. Please run migration: alembic upgrade head"
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to create match result: {error_msg}"
                )
        else:
            # Update existing match result
            try:
                match_result.shortlisted = shortlisted
                
                # If unshortlisting, also disable interview
                if not shortlisted:
                    match_result.interview_enabled = False
                    match_result.online_interview_enabled = False
            except Exception as update_error:
                db.rollback()
                error_msg = str(update_error)
                logger.error(f"Error updating match_result: {error_msg}", exc_info=True)
                # Check if it's a column missing error
                if 'column' in error_msg.lower() and ('interview_enabled' in error_msg or 'shortlisted' in error_msg):
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Database schema mismatch. Please run migration: alembic upgrade head"
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to update match result: {error_msg}"
                )
        
        try:
            db.commit()
            db.refresh(match_result)
        except Exception as commit_error:
            db.rollback()
            error_msg = str(commit_error)
            logger.error(f"Database commit failed: {error_msg}", exc_info=True)
            # Check if it's a column missing error
            if 'column' in error_msg.lower() and ('interview_enabled' in error_msg or 'shortlisted' in error_msg):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database schema mismatch. Please run migration: alembic upgrade head"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to save shortlist status: {error_msg}"
            )
        
        logger.info(f"Candidate {candidate_id} {'shortlisted' if shortlisted else 'unshortlisted'} successfully")
        
        return {
            "candidate_id": str(candidate_id),
            "job_id": str(job_id),
            "shortlisted": match_result.shortlisted,
            "interview_enabled": match_result.interview_enabled,
            "message": f"Candidate {'shortlisted' if shortlisted else 'unshortlisted'} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(f"Error shortlisting candidate: {error_msg}", exc_info=True)
        # Check if it's a column missing error
        if 'column' in error_msg.lower() and ('interview_enabled' in error_msg or 'shortlisted' in error_msg):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database schema mismatch. Please run migration: alembic upgrade head"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error shortlisting candidate: {error_msg}"
        )


@router.post("/{candidate_id}/toggle-interview", status_code=status.HTTP_200_OK)
async def toggle_interview(
    candidate_id: UUID,
    job_id: UUID = Query(..., description="Job ID"),
    toggle_data: InterviewToggleRequest = ...,  # Make body required
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Toggle interview enabled status for a candidate
    
    Rules:
    - Candidate must be shortlisted
    - When interview_enabled = false, online_interview_enabled is also set to false
    
    This endpoint requires match_result to exist (candidate must be shortlisted first).
    """
    try:
        logger.info(f"Toggling interview for candidate {candidate_id}, job {job_id} by user {current_user.email}")
        logger.debug(f"Toggle data: interview_enabled={toggle_data.interview_enabled}, online_interview_enabled={toggle_data.online_interview_enabled}")
        
        # Query for existing match result
        match_result = db.query(MatchResult).filter(
            MatchResult.job_id == job_id,
            MatchResult.candidate_id == candidate_id
        ).first()
        
        # If match_result doesn't exist, create it (but candidate must be shortlisted first)
        if not match_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate must be shortlisted first. Please shortlist the candidate before enabling interview."
            )
        
        # Check if candidate is shortlisted
        if not match_result.shortlisted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate must be shortlisted before enabling interview"
            )
        
        # Update interview enabled status
        match_result.interview_enabled = toggle_data.interview_enabled
        
        # Update online interview enabled
        if toggle_data.online_interview_enabled is not None:
            # Can only enable online if interview is enabled
            if toggle_data.online_interview_enabled and not toggle_data.interview_enabled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot enable online interview when interview is disabled"
                )
            match_result.online_interview_enabled = toggle_data.online_interview_enabled
        else:
            # If interview is disabled, also disable online
            if not toggle_data.interview_enabled:
                match_result.online_interview_enabled = False
        
        try:
            db.commit()
            db.refresh(match_result)
        except Exception as commit_error:
            db.rollback()
            logger.error(f"Database commit failed: {str(commit_error)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to save interview status: {str(commit_error)}"
            )
        
        logger.info(f"Interview toggled: enabled={match_result.interview_enabled}, online={match_result.online_interview_enabled}")
        
        return {
            "candidate_id": str(candidate_id),
            "job_id": str(job_id),
            "interview_enabled": match_result.interview_enabled,
            "online_interview_enabled": match_result.online_interview_enabled,
            "message": "Interview status updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error toggling interview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error toggling interview: {str(e)}"
        )


@router.get("/{candidate_id}/interview-status")
async def get_candidate_interview_status(
    candidate_id: UUID,
    job_id: UUID = Query(..., description="Job ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get interview status for a candidate
    
    Returns default values if match_result doesn't exist (no 404 error).
    """
    try:
        match_result = db.query(MatchResult).filter(
            MatchResult.job_id == job_id,
            MatchResult.candidate_id == candidate_id
        ).first()
        
        # Return defaults if match_result doesn't exist (don't raise 404)
        if not match_result:
            return {
                "candidate_id": str(candidate_id),
                "job_id": str(job_id),
                "shortlisted": False,
                "interview_enabled": False,
                "online_interview_enabled": False
            }
        
        return {
            "candidate_id": str(candidate_id),
            "job_id": str(job_id),
            "shortlisted": match_result.shortlisted,
            "interview_enabled": match_result.interview_enabled,
            "online_interview_enabled": match_result.online_interview_enabled
        }
        
    except Exception as e:
        logger.error(f"Error getting interview status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error retrieving status: {str(e)}"
        )

