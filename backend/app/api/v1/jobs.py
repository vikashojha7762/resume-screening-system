"""
Job management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.job import Job, JobStatus
from app.models.user import User
from app.schemas.job import JobCreate, JobUpdate, Job as JobSchema, JobListResponse
from app.core.dependencies import get_current_active_user
from app.services.candidate_matcher import candidate_matcher
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


class CandidateMatchResult(BaseModel):
    """Individual candidate match result"""
    candidate_id: str
    anonymized_id: str
    resume_id: str
    resume_file_name: str
    candidate_name: str
    final_score: float
    rank: int
    component_scores: Dict[str, float]
    matched_skills: List[str]
    missing_skills: List[str]
    experience_summary: str


class MatchCandidatesResponse(BaseModel):
    """Response for match candidates endpoint"""
    job_id: str
    job_title: str
    candidates_matched: int
    ranked_candidates: List[CandidateMatchResult]
    matching_weights: Dict[str, float]
    message: Optional[str] = None


@router.post("", response_model=JobSchema, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new job posting
    """
    new_job = Job(
        title=job_data.title,
        description=job_data.description,
        requirements_json=job_data.requirements_json,
        status=job_data.status or JobStatus.DRAFT,
        created_by=current_user.id
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    logger.info(f"Job created: {new_job.id} by user {current_user.email}")
    return new_job


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),  # Support both pageSize and page_size
    status_filter: JobStatus = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all jobs with pagination and filtering
    """
    try:
        logger.info(f"Listing jobs - Page: {page}, PageSize: {page_size}, StatusFilter: {status_filter}, User: {current_user.email}")
        
        query = db.query(Job)
        
        # Filter by status if provided
        if status_filter:
            query = query.filter(Job.status == status_filter)
        
        # Get total count
        try:
            total = query.count()
            logger.debug(f"Total jobs found: {total}")
        except Exception as count_error:
            logger.error(f"Error counting jobs: {str(count_error)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error counting jobs: {str(count_error)}"
            )
        
        # Apply pagination
        try:
            jobs = query.order_by(desc(Job.created_at)).offset((page - 1) * page_size).limit(page_size).all()
            logger.debug(f"Retrieved {len(jobs)} jobs")
        except Exception as query_error:
            logger.error(f"Error querying jobs: {str(query_error)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving jobs: {str(query_error)}"
            )
        
        # Ensure requirements_json has defaults for all jobs
        for job in jobs:
            if job.requirements_json is None:
                job.requirements_json = {
                    "required_skills": [],
                    "preferred_skills": [],
                    "required_experience_years": 0,
                    "preferred_experience_years": 0
                }
        
        return JobListResponse(
            items=jobs,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error listing jobs: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing jobs: {error_msg}"
        )


@router.get("/{job_id}", response_model=JobSchema)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific job by ID
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.put("/{job_id}", response_model=JobSchema)
async def update_job(
    job_id: UUID,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a job posting
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Update fields
    if job_data.title is not None:
        job.title = job_data.title
    if job_data.description is not None:
        job.description = job_data.description
    if job_data.requirements_json is not None:
        job.requirements_json = job_data.requirements_json
    if job_data.status is not None:
        job.status = job_data.status
    
    db.commit()
    db.refresh(job)
    
    logger.info(f"Job updated: {job.id} by user {current_user.email}")
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a job posting
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    db.delete(job)
    db.commit()
    
    logger.info(f"Job deleted: {job_id} by user {current_user.email}")


@router.post("/{job_id}/match-candidates", response_model=MatchCandidatesResponse)
async def match_candidates_to_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Match all processed candidates to a job using weighted scoring:
    - Skills: 50%
    - Experience: 30%
    - Semantic Similarity: 20%
    
    Returns ranked list of candidates with match scores and details.
    """
    try:
        # Verify job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if job is active
        if job.status != JobStatus.ACTIVE:
            logger.warning(f"Job {job_id} is not active (status: {job.status})")
        
        logger.info(f"Matching candidates to job {job_id} by user {current_user.email}")
        
        # Perform matching
        match_results = candidate_matcher.match_candidates_to_job(
            job_id=str(job_id),
            db=db
        )
        
        # Convert to response format
        ranked_candidates = []
        for candidate in match_results.get('ranked_candidates', []):
            try:
                # Ensure all required fields are present with defaults
                candidate_data = {
                    'candidate_id': str(candidate.get('candidate_id', '')),
                    'anonymized_id': str(candidate.get('anonymized_id', '')),
                    'resume_id': str(candidate.get('resume_id', '')),
                    'resume_file_name': str(candidate.get('resume_file_name', '')),
                    'candidate_name': str(candidate.get('candidate_name', 'Anonymous')),
                    'final_score': float(candidate.get('final_score', 0.0)),
                    'rank': int(candidate.get('rank', 0)),
                    'component_scores': dict(candidate.get('component_scores', {})),
                    'matched_skills': list(candidate.get('matched_skills', [])),
                    'missing_skills': list(candidate.get('missing_skills', [])),
                    'experience_summary': str(candidate.get('experience_summary', ''))
                }
                ranked_candidates.append(CandidateMatchResult(**candidate_data))
            except Exception as e:
                logger.error(f"Error creating CandidateMatchResult: {str(e)}", exc_info=True)
                logger.error(f"Candidate data: {candidate}")
                # Skip invalid candidates
                continue
        
        return MatchCandidatesResponse(
            job_id=str(match_results.get('job_id', job_id)),
            job_title=str(match_results.get('job_title', job.title)),
            candidates_matched=int(match_results.get('candidates_matched', len(ranked_candidates))),
            ranked_candidates=ranked_candidates,
            matching_weights=dict(match_results.get('matching_weights', {'skills': 0.5, 'experience': 0.3, 'semantic': 0.2})),
            message=match_results.get('message')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching candidates to job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during candidate matching: {str(e)}"
        )

