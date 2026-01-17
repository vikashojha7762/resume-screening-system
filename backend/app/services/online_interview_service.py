"""
Online Interview Service
Handles online interview link generation and access control
"""
import logging
import uuid
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.interview import Interview, InterviewStatus

logger = logging.getLogger(__name__)


class OnlineInterviewService:
    """
    Manages online interview links and access
    Supports multiple providers (INTERNAL, ZOOM, GOOGLE_MEET)
    """
    
    def __init__(self):
        # Provider configuration
        self.provider = "INTERNAL_VIDEO_ROOM"  # Default provider
        self.base_url = "https://interview.example.com"  # Base URL for interview links
        self.link_validity_hours = 24  # Links valid for 24 hours
        
    def generate_meeting_link(
        self,
        interview_id: str,
        job_title: str,
        candidate_id: str
    ) -> Dict[str, Any]:
        """
        Generate a secure meeting link for online interview
        
        Args:
            interview_id: Interview ID
            job_title: Job title for context
            candidate_id: Candidate ID
            
        Returns:
            Dictionary with meeting_link and meeting_room_id
        """
        try:
            # Generate unique room ID
            room_id = self._generate_secure_room_id(interview_id, candidate_id)
            
            # Generate secure meeting link based on provider
            if self.provider == "INTERNAL_VIDEO_ROOM":
                meeting_link = f"{self.base_url}/room/{room_id}"
            elif self.provider == "ZOOM":
                # Placeholder for future Zoom integration
                meeting_link = f"https://zoom.us/j/{room_id}"
            elif self.provider == "GOOGLE_MEET":
                # Placeholder for future Google Meet integration
                meeting_link = f"https://meet.google.com/{room_id}"
            else:
                # Default to internal
                meeting_link = f"{self.base_url}/room/{room_id}"
            
            logger.info(f"Generated meeting link for interview {interview_id}: {meeting_link}")
            
            return {
                'meeting_link': meeting_link,
                'meeting_room_id': room_id,
                'provider': self.provider,
                'expires_at': (datetime.now(timezone.utc) + timedelta(hours=self.link_validity_hours)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating meeting link: {str(e)}", exc_info=True)
            raise
    
    def validate_meeting_access(
        self,
        meeting_room_id: str,
        interview: Interview,
        participant_type: str
    ) -> Dict[str, Any]:
        """
        Validate if a participant can access the meeting
        
        Args:
            meeting_room_id: Meeting room ID
            interview: Interview object
            participant_type: 'candidate' or 'interviewer'
            
        Returns:
            Dictionary with can_join, message, and access details
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Check room ID matches
            if interview.meeting_room_id != meeting_room_id:
                return {
                    'can_join': False,
                    'message': 'Invalid meeting room ID',
                    'reason': 'INVALID_ROOM_ID'
                }
            
            # Check interview status
            if interview.interview_status not in [InterviewStatus.SCHEDULED, InterviewStatus.IN_PROGRESS]:
                return {
                    'can_join': False,
                    'message': f'Interview is {interview.interview_status.value}. Cannot join.',
                    'reason': 'INVALID_STATUS'
                }
            
            # Check if online interview is enabled
            if not interview.online_interview_enabled:
                return {
                    'can_join': False,
                    'message': 'Online interview is not enabled for this interview',
                    'reason': 'ONLINE_DISABLED'
                }
            
            # Check if interview is scheduled
            if interview.interview_date is None:
                return {
                    'can_join': False,
                    'message': 'Interview date not set',
                    'reason': 'NO_DATE'
                }
            
            # Calculate time window (allow 15 minutes before and after duration)
            interview_start = interview.interview_date - timedelta(minutes=15)
            interview_end = interview.interview_date + timedelta(minutes=interview.interview_duration + 15)
            
            # Check if current time is within allowed window
            if now < interview_start:
                minutes_until = int((interview_start - now).total_seconds() / 60)
                return {
                    'can_join': False,
                    'message': f'Interview starts in {minutes_until} minutes. Please wait.',
                    'reason': 'TOO_EARLY',
                    'minutes_until': minutes_until,
                    'interview_start': interview_start.isoformat()
                }
            
            if now > interview_end:
                return {
                    'can_join': False,
                    'message': 'Interview time window has expired',
                    'reason': 'EXPIRED'
                }
            
            # All checks passed
            return {
                'can_join': True,
                'message': 'Access granted',
                'reason': 'VALID',
                'interview_start': interview.interview_date.isoformat(),
                'interview_end': interview_end.isoformat(),
                'time_remaining_minutes': int((interview_end - now).total_seconds() / 60)
            }
            
        except Exception as e:
            logger.error(f"Error validating meeting access: {str(e)}", exc_info=True)
            return {
                'can_join': False,
                'message': f'Error validating access: {str(e)}',
                'reason': 'ERROR'
            }
    
    def _generate_secure_room_id(
        self,
        interview_id: str,
        candidate_id: str
    ) -> str:
        """
        Generate a secure, unguessable room ID
        
        Uses:
        - Interview ID
        - Candidate ID
        - Random UUID
        - Hash for security
        """
        # Combine IDs with random component
        combined = f"{interview_id}:{candidate_id}:{uuid.uuid4().hex}"
        
        # Hash for security
        hash_obj = hashlib.sha256(combined.encode())
        hash_hex = hash_obj.hexdigest()[:16]  # Use first 16 chars
        
        # Create readable room ID
        room_id = f"room-{hash_hex}"
        
        return room_id


# Singleton instance
online_interview_service = OnlineInterviewService()

