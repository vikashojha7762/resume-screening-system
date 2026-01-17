"""
Audit Logging System for Compliance
Logs all matching activities for audit and compliance
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
import json

logger = logging.getLogger(__name__)


class AuditLogger:
    """Log matching activities for compliance"""
    
    def __init__(self):
        self.audit_logger = logging.getLogger('audit')
        self.audit_logger.setLevel(logging.INFO)
    
    def log_matching_event(
        self,
        event_type: str,
        job_id: str,
        user_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a matching event for audit
        
        Args:
            event_type: Type of event (match_initiated, match_completed, etc.)
            job_id: Job ID
            user_id: User who initiated the action
            candidate_id: Candidate ID (if applicable)
            details: Additional event details
        """
        try:
            audit_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'job_id': job_id,
                'user_id': user_id,
                'candidate_id': candidate_id,
                'details': details or {}
            }
            
            # Log to file
            self.audit_logger.info(json.dumps(audit_entry))
            
            # Optionally store in database
            # self._store_in_database(audit_entry)
            
        except Exception as e:
            logger.error(f"Error logging audit event: {str(e)}")
    
    def log_bias_detection(
        self,
        job_id: str,
        bias_results: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> None:
        """Log bias detection results"""
        self.log_matching_event(
            event_type='bias_detection',
            job_id=job_id,
            user_id=user_id,
            details={
                'bias_score': bias_results.get('overall_bias_score', 0.0),
                'gender_bias': bias_results.get('gender_bias', {}).get('score', 0.0),
                'age_bias': bias_results.get('age_bias', {}).get('score', 0.0),
                'institution_bias': bias_results.get('institution_bias', {}).get('score', 0.0)
            }
        )
    
    def log_match_result(
        self,
        job_id: str,
        candidate_id: str,
        score: float,
        user_id: Optional[str] = None
    ) -> None:
        """Log individual match result"""
        self.log_matching_event(
            event_type='match_result',
            job_id=job_id,
            candidate_id=candidate_id,
            user_id=user_id,
            details={'score': score}
        )
    
    def log_ranking_change(
        self,
        job_id: str,
        candidate_id: str,
        old_rank: int,
        new_rank: int,
        user_id: Optional[str] = None
    ) -> None:
        """Log ranking changes"""
        self.log_matching_event(
            event_type='ranking_change',
            job_id=job_id,
            candidate_id=candidate_id,
            user_id=user_id,
            details={
                'old_rank': old_rank,
                'new_rank': new_rank
            }
        )


# Singleton instance
audit_logger = AuditLogger()

