"""
Resume management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.resume import Resume, ResumeStatus
from app.models.user import User
from app.schemas.resume import Resume as ResumeSchema, ResumeListResponse, ResumeUploadResponse
from app.core.dependencies import get_current_active_user
from app.services.file_service import file_service
from app.tasks.resume_tasks import process_resume
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeSchema, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a resume file
    """
    try:
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Upload file
        try:
            file_path = file_service.upload_file(
                file_content=file_content,
                filename=file.filename,
                user_id=str(current_user.id)
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"File upload error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
        
        # Create resume record
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        try:
            new_resume = Resume(
                file_path=file_path,
                file_name=file.filename,
                file_size=str(len(file_content)),
                file_type=file_ext,
                status=ResumeStatus.UPLOADED,
                uploaded_by=current_user.id
            )
            
            logger.info(f"Creating resume record: file_name={file.filename}, user_id={current_user.id}")
            db.add(new_resume)
            db.flush()  # Flush to get the ID without committing
            
            logger.info(f"Resume record added to session, ID: {new_resume.id}")
            
            # Commit the transaction
            db.commit()
            logger.info(f"Resume record committed to database: {new_resume.id}")
            
            # Refresh to get all fields from database
            db.refresh(new_resume)
            logger.info(f"Resume record refreshed: {new_resume.id}, status={new_resume.status}")
            
        except Exception as db_error:
            db.rollback()
            logger.error(f"Database error creating resume: {str(db_error)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save resume to database: {str(db_error)}"
            )
        
        # Queue processing task (optional - don't fail if Celery is not available)
        try:
            process_resume.delay(str(new_resume.id))
            logger.info(f"Resume processing queued: {new_resume.id}")
        except Exception as e:
            # Don't fail the upload if Celery is not available
            logger.warning(f"Failed to queue processing task (continuing anyway): {str(e)}")
            # Keep status as UPLOADED even if processing queue fails
        
        logger.info(f"Resume uploaded: {new_resume.id} by user {current_user.email}")
        
        # Return full resume data using from_attributes (Pydantic v2)
        # The schema has model_config = ConfigDict(from_attributes=True) so it can convert from SQLAlchemy model
        try:
            resume_schema = ResumeSchema.model_validate(new_resume)
            logger.info(f"Resume schema created successfully: {resume_schema.id}")
            return resume_schema
        except Exception as validation_error:
            logger.error(f"Schema validation error: {str(validation_error)}", exc_info=True)
            logger.error(f"Resume object: id={new_resume.id}, status={new_resume.status}, type={type(new_resume.status)}")
            # Fallback: manually construct the response with proper type conversions
            try:
                # Convert enum to string value if needed
                status_value = new_resume.status.value if hasattr(new_resume.status, 'value') else str(new_resume.status)
                
                resume_data = ResumeSchema(
                    id=new_resume.id,
                    file_path=new_resume.file_path,
                    file_name=new_resume.file_name,
                    file_size=new_resume.file_size,
                    file_type=new_resume.file_type,
                    parsed_data_json=new_resume.parsed_data_json,
                    status=status_value,  # Use string value
                    uploaded_by=new_resume.uploaded_by,
                    created_at=new_resume.created_at,
                    updated_at=new_resume.updated_at,
                )
                logger.info(f"Fallback resume schema created: {resume_data.id}")
                return resume_data
            except Exception as fallback_error:
                logger.error(f"Fallback serialization also failed: {str(fallback_error)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to serialize resume data: {str(validation_error)}"
                )
    except HTTPException:
        # Re-raise HTTP exceptions (they already have proper status codes)
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in upload_resume: {str(e)}", exc_info=True)
        # Rollback any pending database changes
        try:
            db.rollback()
            logger.info("Database transaction rolled back due to error")
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {str(rollback_error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: ResumeStatus = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all resumes with pagination and filtering
    """
    try:
        query = db.query(Resume).filter(Resume.uploaded_by == current_user.id)
        
        # Filter by status if provided
        if status_filter:
            query = query.filter(Resume.status == status_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        resumes = query.order_by(desc(Resume.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return ResumeListResponse(
            items=resumes,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error listing resumes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resumes: {str(e)}"
        )


@router.get("/{resume_id}", response_model=ResumeSchema)
async def get_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific resume by ID
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a resume and its file
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Delete file
    file_service.delete_file(resume.file_path)
    
    # Delete database record
    db.delete(resume)
    db.commit()
    
    logger.info(f"Resume deleted: {resume_id} by user {current_user.email}")

