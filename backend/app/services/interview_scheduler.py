"""
Interview Scheduling Service
Handles interview scheduling, validation, and status management
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.interview import Interview, InterviewType, InterviewStatus, InterviewLog
from app.models.match_result import MatchResult
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.user import User

logger = logging.getLogger(__name__)


class InterviewScheduler:
    """
    Manages interview scheduling and status updates
    """
    
    def __init__(self):
        # Configuration
        self.min_advance_notice_hours = 2  # Minimum hours before interview can be scheduled
        self.max_advance_days = 90  # Maximum days in advance
    
    def schedule_interview(
        self,
        job_id: UUID,
        candidate_id: UUID,
        interview_date: datetime,
        interview_time: str,
        interview_timezone: str,
        interview_duration: int,
        interviewer_name: Optional[str],
        interview_type: InterviewType,
        online_interview_enabled: bool,
        scheduled_by: UUID,
        notes: Optional[str],
        db: Session
    ) -> Interview:
        """
        Schedule a new interview
        
        Args:
            job_id: Job ID
            candidate_id: Candidate ID
            interview_date: Interview date
            interview_time: Interview time (HH:MM)
            interview_timezone: Timezone
            interview_duration: Duration in minutes
            interviewer_name: Name of interviewer
            interview_type: ONLINE or OFFLINE
            online_interview_enabled: Whether online interview is enabled
            scheduled_by: User ID who scheduled
            notes: Additional notes
            db: Database session
            
        Returns:
            Created Interview object
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate job exists
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Validate candidate exists
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            # Check if candidate is shortlisted and interview enabled
            match_result = db.query(MatchResult).filter(
                MatchResult.job_id == job_id,
                MatchResult.candidate_id == candidate_id
            ).first()
            
            if not match_result:
                raise ValueError(f"Match result not found for job {job_id} and candidate {candidate_id}")
            
            if not match_result.shortlisted:
                raise ValueError("Candidate must be shortlisted before scheduling interview")
            
            if not match_result.interview_enabled:
                raise ValueError("Interview must be enabled for this candidate before scheduling")
            
            # Validate interview date is in the future
            now = datetime.now(timezone.utc)
            interview_datetime = self._combine_date_time(interview_date, interview_time, interview_timezone)
            
            if interview_datetime <= now:
                raise ValueError("Interview date and time must be in the future")
            
            # Validate minimum advance notice
            min_datetime = now + timedelta(hours=self.min_advance_notice_hours)
            if interview_datetime < min_datetime:
                raise ValueError(f"Interview must be scheduled at least {self.min_advance_notice_hours} hours in advance")
            
            # Validate maximum advance notice
            max_datetime = now + timedelta(days=self.max_advance_days)
            if interview_datetime > max_datetime:
                raise ValueError(f"Interview cannot be scheduled more than {self.max_advance_days} days in advance")
            
            # Check for conflicting interviews
            existing_interview = db.query(Interview).filter(
                Interview.candidate_id == candidate_id,
                Interview.interview_status == InterviewStatus.SCHEDULED,
                Interview.interview_date == interview_datetime
            ).first()
            
            if existing_interview:
                raise ValueError("Candidate already has an interview scheduled at this time")
            
            # Create interview
            new_interview = Interview(
                job_id=job_id,
                candidate_id=candidate_id,
                interview_date=interview_datetime,
                interview_time=interview_time,
                interview_timezone=interview_timezone,
                interview_duration=interview_duration,
                interviewer_name=interviewer_name,
                interview_type=interview_type,
                interview_status=InterviewStatus.SCHEDULED,
                online_interview_enabled=online_interview_enabled,
                scheduled_by=scheduled_by,
                notes=notes
            )
            
            # Generate meeting link if online interview is enabled
            if online_interview_enabled and interview_type == InterviewType.ONLINE:
                from app.services.online_interview_service import online_interview_service
                meeting_data = online_interview_service.generate_meeting_link(
                    interview_id=str(new_interview.id),
                    job_title=job.title,
                    candidate_id=str(candidate_id)
                )
                new_interview.meeting_link = meeting_data['meeting_link']
                new_interview.meeting_room_id = meeting_data['meeting_room_id']
            
            db.add(new_interview)
            db.commit()
            db.refresh(new_interview)
            
            # Log the scheduling action
            self._log_interview_action(
                interview_id=new_interview.id,
                action="SCHEDULED",
                action_by=scheduled_by,
                new_values={
                    'interview_date': interview_datetime.isoformat(),
                    'interview_type': interview_type.value,
                    'online_interview_enabled': online_interview_enabled
                },
                db=db
            )
            
            logger.info(f"Interview scheduled: {new_interview.id} for candidate {candidate_id} on {interview_datetime}")
            
            return new_interview
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error scheduling interview: {str(e)}", exc_info=True)
            raise
    
    def update_interview(
        self,
        interview_id: UUID,
        updates: Dict[str, Any],
        updated_by: UUID,
        db: Session
    ) -> Interview:
        """
        Update an existing interview (reschedule or update details)
        
        Args:
            interview_id: Interview ID
            updates: Dictionary of fields to update
            updated_by: User ID making the update
            db: Database session
            
        Returns:
            Updated Interview object
        """
        try:
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            # Store old values for logging
            old_values = {
                'interview_date': interview.interview_date.isoformat() if interview.interview_date else None,
                'interview_time': interview.interview_time,
                'interview_duration': interview.interview_duration,
                'interview_status': interview.interview_status.value if interview.interview_status else None,
            }
            
            # Update fields
            if 'interview_date' in updates:
                interview_date = updates['interview_date']
                interview_time = updates.get('interview_time', interview.interview_time)
                interview_timezone = updates.get('interview_timezone', interview.interview_timezone)
                interview_datetime = self._combine_date_time(interview_date, interview_time, interview_timezone)
                
                # Validate future date
                now = datetime.now(timezone.utc)
                if interview_datetime <= now:
                    raise ValueError("Interview date and time must be in the future")
                
                interview.interview_date = interview_datetime
            
            if 'interview_time' in updates:
                interview.interview_time = updates['interview_time']
            
            if 'interview_timezone' in updates:
                interview.interview_timezone = updates['interview_timezone']
            
            if 'interview_duration' in updates:
                interview.interview_duration = updates['interview_duration']
            
            if 'interviewer_name' in updates:
                interview.interviewer_name = updates['interviewer_name']
            
            if 'interview_type' in updates:
                interview.interview_type = updates['interview_type']
            
            if 'online_interview_enabled' in updates:
                interview.online_interview_enabled = updates['online_interview_enabled']
                # Regenerate meeting link if online is enabled
                if updates['online_interview_enabled'] and interview.interview_type == InterviewType.ONLINE:
                    from app.services.online_interview_service import online_interview_service
                    job = db.query(Job).filter(Job.id == interview.job_id).first()
                    meeting_data = online_interview_service.generate_meeting_link(
                        interview_id=str(interview.id),
                        job_title=job.title if job else "Interview",
                        candidate_id=str(interview.candidate_id)
                    )
                    interview.meeting_link = meeting_data['meeting_link']
                    interview.meeting_room_id = meeting_data['meeting_room_id']
            
            if 'interview_status' in updates:
                interview.interview_status = updates['interview_status']
            
            if 'cancellation_reason' in updates:
                interview.cancellation_reason = updates['cancellation_reason']
            
            if 'notes' in updates:
                interview.notes = updates['notes']
            
            db.commit()
            db.refresh(interview)
            
            # Log the update
            new_values = {
                'interview_date': interview.interview_date.isoformat() if interview.interview_date else None,
                'interview_time': interview.interview_time,
                'interview_duration': interview.interview_duration,
                'interview_status': interview.interview_status.value if interview.interview_status else None,
            }
            
            self._log_interview_action(
                interview_id=interview.id,
                action="RESCHEDULED" if 'interview_date' in updates else "UPDATED",
                action_by=updated_by,
                old_values=old_values,
                new_values=new_values,
                db=db
            )
            
            logger.info(f"Interview updated: {interview.id} by user {updated_by}")
            
            return interview
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating interview: {str(e)}", exc_info=True)
            raise
    
    def cancel_interview(
        self,
        interview_id: UUID,
        cancellation_reason: Optional[str],
        cancelled_by: UUID,
        db: Session
    ) -> Interview:
        """
        Cancel an interview
        
        Args:
            interview_id: Interview ID
            cancellation_reason: Reason for cancellation
            cancelled_by: User ID cancelling
            db: Database session
            
        Returns:
            Cancelled Interview object
        """
        try:
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            if interview.interview_status == InterviewStatus.CANCELLED:
                raise ValueError("Interview is already cancelled")
            
            if interview.interview_status == InterviewStatus.COMPLETED:
                raise ValueError("Cannot cancel a completed interview")
            
            old_status = interview.interview_status.value
            
            interview.interview_status = InterviewStatus.CANCELLED
            interview.cancellation_reason = cancellation_reason
            
            db.commit()
            db.refresh(interview)
            
            # Log cancellation
            self._log_interview_action(
                interview_id=interview.id,
                action="CANCELLED",
                action_by=cancelled_by,
                old_values={'interview_status': old_status},
                new_values={'interview_status': InterviewStatus.CANCELLED.value},
                action_reason=cancellation_reason,
                db=db
            )
            
            logger.info(f"Interview cancelled: {interview.id} by user {cancelled_by}")
            
            return interview
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error cancelling interview: {str(e)}", exc_info=True)
            raise
    
    def mark_attendance(
        self,
        interview_id: UUID,
        participant_type: str,  # 'candidate' or 'interviewer'
        db: Session
    ) -> Interview:
        """
        Mark when a participant joins the interview
        
        Args:
            interview_id: Interview ID
            participant_type: 'candidate' or 'interviewer'
            db: Database session
            
        Returns:
            Updated Interview object
        """
        try:
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            if interview.interview_status != InterviewStatus.SCHEDULED:
                raise ValueError(f"Cannot join interview with status {interview.interview_status.value}")
            
            now = datetime.now(timezone.utc)
            
            if participant_type == 'candidate':
                if interview.candidate_joined_at is None:
                    interview.candidate_joined_at = now
                    interview.interview_status = InterviewStatus.IN_PROGRESS
                    logger.info(f"Candidate joined interview: {interview.id}")
            elif participant_type == 'interviewer':
                if interview.interviewer_joined_at is None:
                    interview.interviewer_joined_at = now
                    if interview.interview_status == InterviewStatus.SCHEDULED:
                        interview.interview_status = InterviewStatus.IN_PROGRESS
                    logger.info(f"Interviewer joined interview: {interview.id}")
            else:
                raise ValueError(f"Invalid participant_type: {participant_type}")
            
            db.commit()
            db.refresh(interview)
            
            # Log attendance
            self._log_interview_action(
                interview_id=interview.id,
                action="JOINED",
                action_by=None,  # Candidate joins without user account
                new_values={
                    'participant_type': participant_type,
                    'joined_at': now.isoformat()
                },
                db=db
            )
            
            return interview
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking attendance: {str(e)}", exc_info=True)
            raise
    
    def update_interview_status_auto(self, db: Session) -> List[Interview]:
        """
        Auto-update interview statuses based on time
        - Mark as COMPLETED if past end time
        - Mark as NO_SHOW if candidate didn't join
        
        Returns:
            List of updated interviews
        """
        try:
            now = datetime.now(timezone.utc)
            updated_interviews = []
            
            # Find scheduled interviews that should be completed
            scheduled_interviews = db.query(Interview).filter(
                Interview.interview_status == InterviewStatus.SCHEDULED
            ).all()
            
            for interview in scheduled_interviews:
                interview_end = interview.interview_date + timedelta(minutes=interview.interview_duration)
                
                # Mark as completed if past end time
                if now > interview_end:
                    if interview.candidate_joined_at is not None:
                        interview.interview_status = InterviewStatus.COMPLETED
                        updated_interviews.append(interview)
                        logger.info(f"Auto-marked interview {interview.id} as COMPLETED")
                    else:
                        # No show if candidate didn't join
                        interview.interview_status = InterviewStatus.NO_SHOW
                        updated_interviews.append(interview)
                        logger.info(f"Auto-marked interview {interview.id} as NO_SHOW")
            
            # Also check in-progress interviews
            in_progress = db.query(Interview).filter(
                Interview.interview_status == InterviewStatus.IN_PROGRESS
            ).all()
            
            for interview in in_progress:
                interview_end = interview.interview_date + timedelta(minutes=interview.interview_duration)
                if now > interview_end:
                    interview.interview_status = InterviewStatus.COMPLETED
                    updated_interviews.append(interview)
                    logger.info(f"Auto-marked interview {interview.id} as COMPLETED")
            
            if updated_interviews:
                db.commit()
                for interview in updated_interviews:
                    db.refresh(interview)
            
            return updated_interviews
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error auto-updating interview statuses: {str(e)}", exc_info=True)
            return []
    
    def _combine_date_time(
        self,
        interview_date: datetime,
        interview_time: str,
        interview_timezone: str
    ) -> datetime:
        """
        Combine date and time string into datetime object with timezone
        """
        try:
            # Parse time string (HH:MM)
            time_parts = interview_time.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            # Combine with date
            if interview_date.tzinfo is None:
                # If date has no timezone, assume UTC
                combined = interview_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                combined = combined.replace(tzinfo=timezone.utc)
            else:
                combined = interview_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Convert to specified timezone if needed
            # For now, we'll use UTC as default
            # In production, use pytz or zoneinfo for proper timezone handling
            return combined
            
        except Exception as e:
            logger.error(f"Error combining date and time: {str(e)}")
            raise ValueError(f"Invalid time format: {interview_time}")
    
    def _log_interview_action(
        self,
        interview_id: UUID,
        action: str,
        action_by: Optional[UUID],
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        action_reason: Optional[str] = None,
        db: Session = None
    ):
        """
        Log an interview action for audit trail
        """
        try:
            log_entry = InterviewLog(
                interview_id=interview_id,
                action=action,
                action_by=action_by,
                action_reason=action_reason,
                old_values=old_values,
                new_values=new_values
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging interview action: {str(e)}", exc_info=True)
            # Don't fail the main operation if logging fails
            db.rollback()


# Singleton instance
interview_scheduler = InterviewScheduler()

