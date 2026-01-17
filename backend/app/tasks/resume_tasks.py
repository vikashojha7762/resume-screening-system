from app.celery_app import celery_app
from app.core.config import settings
from app.database import SessionLocal
from app.models.resume import Resume, ResumeStatus
from app.models.processing_queue import ProcessingQueue, ProcessingStatus
from app.models.candidate import Candidate
from app.services.file_service import file_service
from app.services.nlp_pipeline import nlp_pipeline
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import uuid
from typing import Dict, Any

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.resume_tasks.process_resume",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # 10 minutes max delay
    retry_jitter=True
)
def process_resume(self, resume_id: str):
    """
    Process a single resume file with error handling and retries.
    This task will be called asynchronously to parse and analyze resumes.
    """
    db: Session = SessionLocal()
    
    try:
        logger.info(f"Processing resume with ID: {resume_id}")
        
        # Get resume from database
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            logger.error(f"Resume not found: {resume_id}")
            return {"status": "error", "message": "Resume not found", "resume_id": resume_id}
        
        # Update resume status
        resume.status = ResumeStatus.PARSING
        db.commit()
        
        # Create or update processing queue entry
        queue_entry = db.query(ProcessingQueue).filter(
            ProcessingQueue.resume_id == resume.id
        ).first()
        
        if not queue_entry:
            queue_entry = ProcessingQueue(
                job_id=uuid.uuid4(),  # Placeholder, should be set when matching with job
                resume_id=resume.id,
                status=ProcessingStatus.PROCESSING,
                progress="10"
            )
            db.add(queue_entry)
        else:
            queue_entry.status = ProcessingStatus.PROCESSING
            queue_entry.progress = "10"
            queue_entry.error_message = None
        
        db.commit()
        
        # Step 1: Get file content
        logger.info(f"Loading file content for resume: {resume_id}")
        file_content = get_file_content(resume)
        
        if not file_content:
            raise Exception("Failed to load file content")
        
        queue_entry.progress = "20"
        db.commit()
        
        # Step 2: Run complete NLP pipeline
        logger.info(f"Running NLP pipeline for resume: {resume_id}")
        nlp_result = nlp_pipeline.process_resume(
            file_content=file_content,
            file_type=resume.file_type,
            filename=resume.file_name,
            generate_embeddings=True
        )
        
        if not nlp_result.get('success'):
            raise Exception(f"NLP pipeline failed: {nlp_result.get('errors', [])}")
        
        queue_entry.progress = "70"
        db.commit()
        
        # Step 3: Update resume with parsed data
        logger.info(f"Updating resume with parsed data: {resume_id}")
        parsed_data = {
            'raw_text': nlp_result.get('raw_text', ''),
            'contact_info': nlp_result.get('contact_info', {}),
            'skills': nlp_result.get('skills', {}),
            'experience': nlp_result.get('experience', {}),
            'education': nlp_result.get('education', {}),
            'quality_metrics': nlp_result.get('quality_metrics', {}),
            'processing_metadata': {
                'processing_time': nlp_result.get('processing_time_seconds', 0),
                'components_executed': nlp_result.get('components_executed', []),
                'warnings': nlp_result.get('warnings', [])
            }
        }
        
        resume.parsed_data_json = parsed_data
        resume.status = ResumeStatus.PARSED
        queue_entry.progress = "80"
        db.commit()
        
        # Step 4: Update embedding vector
        logger.info(f"Updating embedding vector for resume: {resume_id}")
        embeddings = nlp_result.get('embeddings', {})
        if embeddings.get('bert'):
            import numpy as np
            embedding_array = np.array(embeddings['bert'])
            resume.embedding_vector = embedding_array.tolist()
            queue_entry.progress = "90"
            db.commit()
        else:
            logger.warning("No BERT embedding generated")
        
        # Step 4: Create candidate record
        logger.info(f"Creating candidate record: {resume_id}")
        candidate = db.query(Candidate).filter(Candidate.resume_id == resume.id).first()
        if not candidate:
            anonymized_id = f"CAND-{uuid.uuid4().hex[:8].upper()}"
            candidate = Candidate(
                anonymized_id=anonymized_id,
                resume_id=resume.id,
                masked_data_json=anonymize_resume_data(parsed_data)
            )
            db.add(candidate)
            db.commit()
        
        # Update status to processed
        resume.status = ResumeStatus.PROCESSED
        queue_entry.status = ProcessingStatus.COMPLETED
        queue_entry.progress = "100"
        queue_entry.processed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Successfully processed resume: {resume_id}")
        return {
            "status": "success",
            "resume_id": resume_id,
            "candidate_id": str(candidate.id),
            "progress": "100"
        }
        
    except Exception as e:
        logger.error(f"Error processing resume {resume_id}: {str(e)}", exc_info=True)
        
        # Update status to error
        try:
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if resume:
                resume.status = ResumeStatus.ERROR
                db.commit()
            
            queue_entry = db.query(ProcessingQueue).filter(
                ProcessingQueue.resume_id == resume_id
            ).first()
            if queue_entry:
                queue_entry.status = ProcessingStatus.FAILED
                queue_entry.error_message = str(e)
                queue_entry.retry_count = str(int(queue_entry.retry_count or "0") + 1)
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {str(db_error)}")
        
        # Retry if not exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying resume processing: {resume_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        else:
            logger.error(f"Max retries exceeded for resume: {resume_id}")
            return {
                "status": "error",
                "resume_id": resume_id,
                "error": str(e),
                "retries": self.request.retries
            }
    finally:
        db.close()


def get_file_content(resume: Resume) -> bytes:
    """Get file content from S3 or local storage"""
    try:
        if resume.file_path.startswith('s3://'):
            # Download from S3
            import boto3
            s3_client = boto3.client('s3')
            bucket, key = resume.file_path.replace('s3://', '').split('/', 1)
            response = s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        else:
            # Read local file
            with open(resume.file_path, 'rb') as f:
                return f.read()
    except Exception as e:
        logger.error(f"Error loading file content: {str(e)}")
        raise


# File content loading and NLP processing are now handled by nlp_pipeline


def anonymize_resume_data(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Anonymize personal information in resume data"""
    masked = parsed_data.copy()
    
    # Mask email
    if "email" in masked:
        masked["email"] = "***@***.***"
    
    # Mask phone
    if "phone" in masked:
        masked["phone"] = "***-***-****"
    
    return masked


@celery_app.task(name="app.tasks.resume_tasks.process_pending_resumes")
def process_pending_resumes():
    """
    Periodic task to process all pending resumes.
    Runs every 5 minutes (configured in celery_app.py).
    """
    db: Session = SessionLocal()
    
    try:
        logger.info("Processing pending resumes...")
        
        # Query pending resumes
        pending_resumes = db.query(Resume).filter(
            Resume.status.in_([ResumeStatus.UPLOADED, ResumeStatus.ERROR])
        ).limit(10).all()  # Process 10 at a time
        
        processed_count = 0
        for resume in pending_resumes:
            try:
                process_resume.delay(str(resume.id))
                processed_count += 1
                logger.info(f"Queued resume for processing: {resume.id}")
            except Exception as e:
                logger.error(f"Failed to queue resume {resume.id}: {str(e)}")
        
        logger.info(f"Pending resumes processing completed: {processed_count} queued")
        return {"status": "success", "processed": processed_count}
        
    except Exception as e:
        logger.error(f"Error processing pending resumes: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.resume_tasks.analyze_resume_with_ai")
def analyze_resume_with_ai(resume_id: str, job_description: str = None):
    """
    Analyze a resume using AI/ML models.
    """
    logger.info(f"Analyzing resume {resume_id} with AI")
    try:
        # TODO: Implement AI analysis
        # - Use BERT/Spacy for NLP
        # - Extract skills, experience, education
        # - Match against job description if provided
        # - Calculate similarity scores
        
        logger.info(f"Successfully analyzed resume: {resume_id}")
        return {
            "status": "success",
            "resume_id": resume_id,
            "score": 0.0,
            "matched_skills": []
        }
    except Exception as e:
        logger.error(f"Error analyzing resume {resume_id}: {str(e)}")
        raise

