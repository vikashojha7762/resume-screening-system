"""
Interview Management Endpoints
Handles interview scheduling, updates, and online interview access
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models.interview import Interview, InterviewStatus, InterviewType, InterviewLog
from app.models.match_result import MatchResult
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.interview import (
    InterviewCreate, InterviewUpdate, Interview as InterviewSchema,
    InterviewListResponse, InterviewJoinRequest, InterviewJoinResponse,
    InterviewToggleRequest, InterviewLogResponse
)
from app.core.dependencies import get_current_active_user
from app.services.interview_scheduler import interview_scheduler
from app.services.online_interview_service import online_interview_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("", response_model=InterviewSchema, status_code=status.HTTP_201_CREATED)
async def schedule_interview(
    interview_data: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Schedule a new interview
    
    Requirements:
    - Candidate must be shortlisted
    - Interview must be enabled for the candidate
    - Interview date must be in the future
    """
    try:
        logger.info(f"Scheduling interview for candidate {interview_data.candidate_id} by user {current_user.email}")
        
        # Validate match result exists and interview is enabled
        match_result = db.query(MatchResult).filter(
            MatchResult.job_id == interview_data.job_id,
            MatchResult.candidate_id == interview_data.candidate_id
        ).first()
        
        if not match_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match result not found. Please run candidate matching first."
            )
        
        if not match_result.shortlisted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate must be shortlisted before scheduling interview"
            )
        
        if not match_result.interview_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview must be enabled for this candidate before scheduling"
            )
        
        # Schedule interview
        interview = interview_scheduler.schedule_interview(
            job_id=interview_data.job_id,
            candidate_id=interview_data.candidate_id,
            interview_date=interview_data.interview_date,
            interview_time=interview_data.interview_time,
            interview_timezone=interview_data.interview_timezone,
            interview_duration=interview_data.interview_duration,
            interviewer_name=interview_data.interviewer_name,
            interview_type=interview_data.interview_type,
            online_interview_enabled=interview_data.online_interview_enabled,
            scheduled_by=current_user.id,
            notes=interview_data.notes,
            db=db
        )
        
        logger.info(f"Interview scheduled successfully: {interview.id}")
        return interview
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error scheduling interview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error scheduling interview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling interview: {str(e)}"
        )


@router.get("", response_model=InterviewListResponse)
async def list_interviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    job_id: Optional[UUID] = Query(None, description="Filter by job ID"),
    candidate_id: Optional[UUID] = Query(None, description="Filter by candidate ID"),
    status_filter: Optional[InterviewStatus] = Query(None, alias="status", description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List interviews with pagination and filtering
    """
    try:
        logger.info(f"Listing interviews - Page: {page}, Filters: job_id={job_id}, candidate_id={candidate_id}, status={status_filter}")
        
        query = db.query(Interview)
        
        # Apply filters
        if job_id:
            query = query.filter(Interview.job_id == job_id)
        if candidate_id:
            query = query.filter(Interview.candidate_id == candidate_id)
        if status_filter:
            query = query.filter(Interview.interview_status == status_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        interviews = query.order_by(desc(Interview.interview_date)).offset((page - 1) * page_size).limit(page_size).all()
        
        logger.debug(f"Retrieved {len(interviews)} interviews")
        
        return InterviewListResponse(
            items=interviews,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing interviews: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing interviews: {str(e)}"
        )


@router.get("/{interview_id}", response_model=InterviewSchema)
async def get_interview(
    interview_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific interview by ID
    """
    try:
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        return interview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving interview: {str(e)}"
        )


@router.put("/{interview_id}", response_model=InterviewSchema)
async def update_interview(
    interview_id: UUID,
    interview_data: InterviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an interview (reschedule or update details)
    """
    try:
        logger.info(f"Updating interview {interview_id} by user {current_user.email}")
        
        # Build update dict from provided fields
        updates = {}
        if interview_data.interview_date is not None:
            updates['interview_date'] = interview_data.interview_date
        if interview_data.interview_time is not None:
            updates['interview_time'] = interview_data.interview_time
        if interview_data.interview_timezone is not None:
            updates['interview_timezone'] = interview_data.interview_timezone
        if interview_data.interview_duration is not None:
            updates['interview_duration'] = interview_data.interview_duration
        if interview_data.interviewer_name is not None:
            updates['interviewer_name'] = interview_data.interviewer_name
        if interview_data.interview_type is not None:
            updates['interview_type'] = interview_data.interview_type
        if interview_data.online_interview_enabled is not None:
            updates['online_interview_enabled'] = interview_data.online_interview_enabled
        if interview_data.interview_status is not None:
            updates['interview_status'] = interview_data.interview_status
        if interview_data.cancellation_reason is not None:
            updates['cancellation_reason'] = interview_data.cancellation_reason
        if interview_data.notes is not None:
            updates['notes'] = interview_data.notes
        
        interview = interview_scheduler.update_interview(
            interview_id=interview_id,
            updates=updates,
            updated_by=current_user.id,
            db=db
        )
        
        return interview
        
    except ValueError as e:
        logger.error(f"Validation error updating interview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating interview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating interview: {str(e)}"
        )


@router.post("/{interview_id}/cancel", response_model=InterviewSchema)
async def cancel_interview(
    interview_id: UUID,
    cancellation_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancel an interview
    """
    try:
        logger.info(f"Cancelling interview {interview_id} by user {current_user.email}")
        
        interview = interview_scheduler.cancel_interview(
            interview_id=interview_id,
            cancellation_reason=cancellation_reason,
            cancelled_by=current_user.id,
            db=db
        )
        
        return interview
        
    except ValueError as e:
        logger.error(f"Validation error cancelling interview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error cancelling interview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling interview: {str(e)}"
        )


@router.post("/{interview_id}/join", response_model=InterviewJoinResponse)
async def join_interview(
    interview_id: UUID,
    join_request: InterviewJoinRequest,
    db: Session = Depends(get_db)
):
    """
    Join an online interview
    
    Can be called by candidate or interviewer
    No authentication required (candidates don't have accounts)
    """
    try:
        logger.info(f"Join request for interview {interview_id}, room {join_request.meeting_room_id}, type: {join_request.participant_type}")
        
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        # Validate meeting access
        access_result = online_interview_service.validate_meeting_access(
            meeting_room_id=join_request.meeting_room_id,
            interview=interview,
            participant_type=join_request.participant_type
        )
        
        if not access_result['can_join']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=access_result['message']
            )
        
        # Mark attendance
        interview = interview_scheduler.mark_attendance(
            interview_id=interview_id,
            participant_type=join_request.participant_type,
            db=db
        )
        
        # Calculate interview end time
        interview_end = interview.interview_date + timedelta(minutes=interview.interview_duration)
        
        return InterviewJoinResponse(
            meeting_link=interview.meeting_link or "",
            meeting_room_id=interview.meeting_room_id or "",
            interview_id=interview.id,
            interview_start_time=interview.interview_date,
            interview_end_time=interview_end,
            can_join=True,
            message="Access granted"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining interview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error joining interview: {str(e)}"
        )


@router.get("/{interview_id}/logs", response_model=List[InterviewLogResponse])
async def get_interview_logs(
    interview_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get audit logs for an interview
    """
    try:
        # Verify interview exists
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        logs = db.query(InterviewLog).filter(
            InterviewLog.interview_id == interview_id
        ).order_by(desc(InterviewLog.created_at)).all()
        
        return logs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interview logs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving logs: {str(e)}"
        )


@router.post("/auto-update-status")
async def auto_update_interview_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Auto-update interview statuses based on time
    Can be called by cron job or scheduled task
    """
    try:
        updated = interview_scheduler.update_interview_status_auto(db)
        
        return {
            "updated_count": len(updated),
            "updated_interviews": [str(i.id) for i in updated]
        }
        
    except Exception as e:
        logger.error(f"Error auto-updating interview statuses: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating statuses: {str(e)}"
        )

