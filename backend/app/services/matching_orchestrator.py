"""
Matching Orchestrator
Orchestrates complete matching pipeline with scoring, ranking, and bias detection
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.services.scoring_engine import scoring_engine
from app.services.ranking_engine import ranking_engine
from app.services.bias_detector import bias_detector
from app.services.optimization import performance_optimizer
from app.services.audit_logger import audit_logger
from app.database import SessionLocal
from app.models.job import Job
from app.models.resume import Resume
from app.models.candidate import Candidate
from app.models.match_result import MatchResult
from app.models.processing_queue import ProcessingQueue, ProcessingStatus
from sqlalchemy.orm import Session
import uuid

logger = logging.getLogger(__name__)


class MatchingOrchestrator:
    """Orchestrate complete matching pipeline"""
    
    def __init__(self):
        self.strategies = {
            'standard': self._standard_matching,
            'fast': self._fast_matching,
            'comprehensive': self._comprehensive_matching
        }
    
    def match_job_to_candidates(
        self,
        job_id: str,
        candidate_ids: Optional[List[str]] = None,
        strategy: str = 'standard',
        weights: Optional[Dict[str, float]] = None,
        diversity_weight: float = 0.0,
        enable_bias_detection: bool = True
    ) -> Dict[str, Any]:
        """
        Match job to candidates using specified strategy
        
        Args:
            job_id: Job ID to match
            candidate_ids: Optional list of candidate IDs (None = all candidates)
            strategy: Matching strategy ('standard', 'fast', 'comprehensive')
            weights: Custom scoring weights
            diversity_weight: Weight for diversity scoring (0-1)
            enable_bias_detection: Enable bias detection in job description
            
        Returns:
            Complete matching results with rankings and explanations
        """
        db: Session = SessionLocal()
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting matching for job {job_id} with strategy {strategy}")
            
            # Get job
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Detect bias in job description
            bias_results = None
            if enable_bias_detection:
                bias_results = bias_detector.detect_job_description_bias(
                    job.description
                )
                logger.info(f"Bias detection score: {bias_results['overall_bias_score']}")
                # Log bias detection
                audit_logger.log_bias_detection(str(job.id), bias_results)
            
            # Get candidates
            if candidate_ids:
                candidates_query = db.query(Candidate).filter(
                    Candidate.id.in_(candidate_ids)
                )
            else:
                # Get all processed candidates
                candidates_query = db.query(Candidate).join(Resume).filter(
                    Resume.status == 'processed'
                )
            
            candidates = candidates_query.all()
            logger.info(f"Found {len(candidates)} candidates to match")
            
            if not candidates:
                return {
                    'job_id': job_id,
                    'candidates_matched': 0,
                    'ranked_results': [],
                    'message': 'No candidates found'
                }
            
            # Prepare job requirements
            job_requirements = {
                'required_skills': job.requirements_json.get('required_skills', []) if job.requirements_json else [],
                'preferred_skills': job.requirements_json.get('preferred_skills', []) if job.requirements_json else [],
                'required_experience_years': job.requirements_json.get('required_experience_years', 0) if job.requirements_json else 0,
                'preferred_experience_years': job.requirements_json.get('preferred_experience_years', 0) if job.requirements_json else 0,
                'required_degree': job.requirements_json.get('required_degree') if job.requirements_json else None,
                'preferred_institutions': job.requirements_json.get('preferred_institutions', []) if job.requirements_json else [],
                'institution_tiers': job.requirements_json.get('institution_tiers', {}) if job.requirements_json else {},
                'mandatory_requirements': job.requirements_json.get('mandatory_requirements', {}) if job.requirements_json else {}
            }
            
            # Execute matching strategy
            if strategy not in self.strategies:
                logger.warning(f"Unknown strategy {strategy}, using standard")
                strategy = 'standard'
            
            match_results = self.strategies[strategy](
                job, candidates, job_requirements, weights, diversity_weight, db
            )
            
            # Rank candidates
            ranked_results = ranking_engine.rank_candidates(
                match_results,
                job_id,
                diversity_weight
            )
            
            # Store results in database
            self._store_match_results(job_id, ranked_results['ranked_candidates'], db)
            
            # Log matching completion
            audit_logger.log_matching_event(
                'match_completed',
                job_id,
                details={
                    'candidates_matched': len(candidates),
                    'strategy': strategy,
                    'processing_time': processing_time
                }
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'job_id': job_id,
                'job_title': job.title,
                'candidates_matched': len(candidates),
                'ranked_results': ranked_results['ranked_candidates'],
                'clusters': ranked_results.get('clusters', {}),
                'bias_detection': bias_results,
                'processing_time_seconds': processing_time,
                'strategy_used': strategy,
                'diversity_enabled': diversity_weight > 0
            }
            
        except Exception as e:
            logger.error(f"Error in matching orchestrator: {str(e)}", exc_info=True)
            return {
                'job_id': job_id,
                'error': str(e),
                'candidates_matched': 0
            }
        finally:
            db.close()
    
    def _standard_matching(
        self,
        job: Job,
        candidates: List[Candidate],
        job_requirements: Dict[str, Any],
        weights: Optional[Dict[str, float]],
        diversity_weight: float,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Standard matching strategy"""
        match_results = []
        
        for candidate in candidates:
            # Get resume data
            resume = db.query(Resume).filter(Resume.id == candidate.resume_id).first()
            if not resume or not resume.parsed_data_json:
                continue
            
            resume_data = resume.parsed_data_json
            
            # Check cache first
            cached_result = performance_optimizer.get_cached_match_result(
                str(job.id),
                str(candidate.id)
            )
            
            if cached_result:
                match_results.append(cached_result)
                continue
            
            # Calculate score
            score_result = scoring_engine.calculate_match_score(
                resume_data,
                job_requirements,
                weights
            )
            
            if not score_result.get('mandatory_met', False):
                continue  # Skip candidates who don't meet mandatory requirements
            
            # Prepare result
            result = {
                'candidate_id': str(candidate.id),
                'anonymized_id': candidate.anonymized_id,
                'resume_id': str(resume.id),
                'resume_data': resume_data,
                'overall_score': score_result['overall_score'],
                'component_scores': score_result['component_scores'],
                'breakdown': score_result['breakdown'],
                'explanation': score_result['explanation']
            }
            
            # Cache result
            performance_optimizer.cache_match_result(
                str(job.id),
                str(candidate.id),
                result
            )
            
            match_results.append(result)
        
        return match_results
    
    def _fast_matching(
        self,
        job: Job,
        candidates: List[Candidate],
        job_requirements: Dict[str, Any],
        weights: Optional[Dict[str, float]],
        diversity_weight: float,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Fast matching strategy using vector similarity"""
        # Use FAISS for fast similarity search
        # Get job embedding
        job_text = f"{job.title} {job.description}"
        job_embedding = embedding_generator.generate_bert_embedding(job_text)
        
        if job_embedding is None:
            # Fallback to standard
            return self._standard_matching(job, candidates, job_requirements, weights, diversity_weight, db)
        
        # Get candidate embeddings
        candidate_embeddings = []
        candidate_list = []
        
        for candidate in candidates:
            resume = db.query(Resume).filter(Resume.id == candidate.resume_id).first()
            if not resume or not resume.parsed_data_json:
                continue
            
            # Get embedding from resume or generate
            resume_data = resume.parsed_data_json
            if resume.embedding_vector:
                embedding = np.array(resume.embedding_vector)
            else:
                # Generate from text
                text = resume_data.get('raw_text', '')
                embedding = embedding_generator.generate_bert_embedding(text)
                if embedding is None:
                    continue
            
            candidate_embeddings.append(embedding)
            candidate_list.append((candidate, resume, resume_data))
        
        if not candidate_embeddings:
            return []
        
        # Build FAISS index
        embeddings_array = np.array(candidate_embeddings).astype('float32')
        index = performance_optimizer.build_faiss_index(embeddings_array)
        
        # Search for similar candidates
        similar_indices = performance_optimizer.search_similar(
            job_embedding,
            k=min(len(candidate_list), 100),
            threshold=0.5
        )
        
        # Get top candidates and calculate detailed scores
        match_results = []
        for idx, similarity in similar_indices[:50]:  # Top 50
            candidate, resume, resume_data = candidate_list[idx]
            
            # Calculate detailed score
            score_result = scoring_engine.calculate_match_score(
                resume_data,
                job_requirements,
                weights
            )
            
            if score_result.get('mandatory_met', False):
                result = {
                    'candidate_id': str(candidate.id),
                    'anonymized_id': candidate.anonymized_id,
                    'resume_id': str(resume.id),
                    'resume_data': resume_data,
                    'overall_score': score_result['overall_score'],
                    'component_scores': score_result['component_scores'],
                    'breakdown': score_result['breakdown'],
                    'explanation': score_result['explanation'],
                    'vector_similarity': similarity
                }
                match_results.append(result)
        
        return match_results
    
    def _comprehensive_matching(
        self,
        job: Job,
        candidates: List[Candidate],
        job_requirements: Dict[str, Any],
        weights: Optional[Dict[str, float]],
        diversity_weight: float,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Comprehensive matching with all features"""
        # Use standard matching but with more detailed analysis
        results = self._standard_matching(
            job, candidates, job_requirements, weights, diversity_weight, db
        )
        
        # Add additional analysis
        for result in results:
            # Add bias mitigation
            resume_data = result['resume_data']
            anonymized = bias_detector.anonymize_resume(resume_data)
            result['anonymized_data'] = anonymized
        
        return results
    
    def _store_match_results(
        self,
        job_id: str,
        ranked_candidates: List[Dict[str, Any]],
        db: Session
    ) -> None:
        """Store match results in database"""
        try:
            for rank, candidate_result in enumerate(ranked_candidates, start=1):
                candidate_id = candidate_result['candidate_id']
                
                # Check if result already exists
                existing = db.query(MatchResult).filter(
                    MatchResult.job_id == job_id,
                    MatchResult.candidate_id == candidate_id
                ).first()
                
                if existing:
                    # Update existing
                    existing.overall_score = candidate_result['overall_score']
                    existing.scores_json = candidate_result.get('component_scores', {})
                    existing.rank = str(rank)
                    existing.explanation = {
                        'text': candidate_result.get('explanation', ''),
                        'breakdown': candidate_result.get('breakdown', {})
                    }
                else:
                    # Create new
                    match_result = MatchResult(
                        job_id=job_id,
                        candidate_id=candidate_id,
                        overall_score=candidate_result['overall_score'],
                        scores_json=candidate_result.get('component_scores', {}),
                        rank=str(rank),
                        explanation={
                            'text': candidate_result.get('explanation', ''),
                            'breakdown': candidate_result.get('breakdown', {})
                        }
                    )
                    db.add(match_result)
            
            db.commit()
            logger.info(f"Stored {len(ranked_candidates)} match results")
            
        except Exception as e:
            logger.error(f"Error storing match results: {str(e)}", exc_info=True)
            db.rollback()


# Singleton instance
matching_orchestrator = MatchingOrchestrator()

