"""
Complete NLP Pipeline Orchestrator
Coordinates all NLP components for resume processing
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.services.resume_parser import resume_parser
from app.services.skill_extractor import skill_extractor
from app.services.experience_parser import experience_parser
from app.services.education_parser import education_parser
from app.ml.embeddings import embedding_generator

logger = logging.getLogger(__name__)


class NLPPipeline:
    """Orchestrate all NLP components for resume processing"""
    
    def __init__(self):
        self.components = {
            'resume_parser': resume_parser,
            'skill_extractor': skill_extractor,
            'experience_parser': experience_parser,
            'education_parser': education_parser,
        }
    
    def process_resume(
        self,
        file_content: bytes,
        file_type: str,
        filename: str = "",
        generate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Complete NLP pipeline for resume processing
        
        Args:
            file_content: Raw file bytes
            file_type: File extension
            filename: Original filename
            generate_embeddings: Whether to generate embeddings
            
        Returns:
            Complete parsed resume data with all extracted information
        """
        start_time = datetime.now()
        result = {
            'success': False,
            'filename': filename,
            'processing_time_seconds': 0,
            'components_executed': [],
            'errors': [],
            'warnings': [],
            'quality_metrics': {}
        }
        
        try:
            logger.info(f"Starting NLP pipeline for {filename}")
            
            # Step 1: Parse resume text
            parsed_data = self._execute_component(
                'resume_parser',
                lambda: resume_parser.parse(file_content, file_type, filename),
                result
            )
            
            if not parsed_data or 'raw_text' not in parsed_data:
                raise ValueError("Failed to extract text from resume")
            
            text = parsed_data['raw_text']
            result['raw_text'] = text
            result['metadata'] = parsed_data.get('metadata', {})
            result['sections'] = parsed_data.get('sections', {})
            
            # Step 2: Extract contact information
            contact_info = self._execute_component(
                'contact_extraction',
                lambda: resume_parser.extract_contact_info(text),
                result
            )
            result['contact_info'] = contact_info or {}
            
            # Step 3: Extract skills
            skills_data = self._execute_component(
                'skill_extractor',
                lambda: skill_extractor.extract_skills(text),
                result
            )
            result['skills'] = skills_data or {}
            
            # Step 4: Extract experience
            experience_data = self._execute_component(
                'experience_parser',
                lambda: experience_parser.extract_experience(text),
                result
            )
            result['experience'] = experience_data or {}
            
            # Step 5: Extract education
            education_data = self._execute_component(
                'education_parser',
                lambda: education_parser.extract_education(text),
                result
            )
            result['education'] = education_data or {}
            
            # Step 6: Generate embeddings
            if generate_embeddings:
                embeddings = self._execute_component(
                    'embedding_generator',
                    lambda: self._generate_embeddings(text),
                    result
                )
                result['embeddings'] = embeddings or {}
            
            # Step 7: Calculate quality metrics
            result['quality_metrics'] = self._calculate_quality_metrics(result)
            
            # Mark as successful
            result['success'] = True
            
            # Calculate processing time
            end_time = datetime.now()
            result['processing_time_seconds'] = (end_time - start_time).total_seconds()
            
            logger.info(
                f"NLP pipeline completed for {filename} in {result['processing_time_seconds']:.2f}s"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error in NLP pipeline for {filename}: {str(e)}", exc_info=True)
            result['errors'].append(str(e))
            result['success'] = False
            
            end_time = datetime.now()
            result['processing_time_seconds'] = (end_time - start_time).total_seconds()
            
            return result
    
    def _execute_component(
        self,
        component_name: str,
        func: callable,
        result: Dict[str, Any]
    ) -> Optional[Any]:
        """Execute a component with error handling"""
        try:
            output = func()
            result['components_executed'].append(component_name)
            return output
        except Exception as e:
            error_msg = f"{component_name} failed: {str(e)}"
            logger.warning(error_msg)
            result['warnings'].append(error_msg)
            return None
    
    def _generate_embeddings(self, text: str) -> Dict[str, Any]:
        """Generate embeddings for resume text"""
        embeddings = {}
        
        # Generate BERT embedding
        try:
            bert_embedding = embedding_generator.generate_bert_embedding(text)
            if bert_embedding is not None:
                embeddings['bert'] = bert_embedding.tolist()
                embeddings['bert_dimension'] = len(bert_embedding)
        except Exception as e:
            logger.warning(f"BERT embedding generation failed: {str(e)}")
        
        # Generate TF-IDF embedding
        try:
            tfidf_embedding = embedding_generator.generate_tfidf_embedding(text, fit=True)
            if tfidf_embedding is not None:
                embeddings['tfidf'] = tfidf_embedding.tolist()
                embeddings['tfidf_dimension'] = len(tfidf_embedding)
        except Exception as e:
            logger.warning(f"TF-IDF embedding generation failed: {str(e)}")
        
        return embeddings
    
    def _calculate_quality_metrics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality metrics for parsed resume"""
        metrics = {
            'completeness_score': 0.0,
            'data_quality_score': 0.0,
            'extraction_success_rate': 0.0
        }
        
        # Calculate completeness
        components = ['contact_info', 'skills', 'experience', 'education']
        completed = sum(1 for comp in components if result.get(comp))
        metrics['completeness_score'] = completed / len(components)
        
        # Calculate data quality
        quality_factors = []
        
        # Check if we have text
        if result.get('raw_text'):
            word_count = len(result['raw_text'].split())
            if word_count > 100:
                quality_factors.append(1.0)
            elif word_count > 50:
                quality_factors.append(0.7)
            else:
                quality_factors.append(0.3)
        
        # Check skills extraction
        if result.get('skills', {}).get('total_skills', 0) > 0:
            quality_factors.append(1.0)
        elif result.get('skills'):
            quality_factors.append(0.5)
        
        # Check experience extraction
        if result.get('experience', {}).get('experience_count', 0) > 0:
            quality_factors.append(1.0)
        elif result.get('experience'):
            quality_factors.append(0.5)
        
        # Check education extraction
        if result.get('education', {}).get('total_degrees', 0) > 0:
            quality_factors.append(1.0)
        elif result.get('education'):
            quality_factors.append(0.5)
        
        if quality_factors:
            metrics['data_quality_score'] = sum(quality_factors) / len(quality_factors)
        
        # Calculate extraction success rate
        total_components = len(result.get('components_executed', []))
        expected_components = 5  # parser, contact, skills, experience, education
        if expected_components > 0:
            metrics['extraction_success_rate'] = total_components / expected_components
        
        return metrics
    
    def process_batch(
        self,
        resumes: List[Dict[str, bytes]],
        generate_embeddings: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process multiple resumes in batch
        
        Args:
            resumes: List of dicts with 'content', 'type', 'filename'
            generate_embeddings: Whether to generate embeddings
            
        Returns:
            List of processed resume results
        """
        results = []
        
        for resume in resumes:
            try:
                result = self.process_resume(
                    file_content=resume['content'],
                    file_type=resume['type'],
                    filename=resume.get('filename', ''),
                    generate_embeddings=generate_embeddings
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing resume in batch: {str(e)}")
                results.append({
                    'success': False,
                    'filename': resume.get('filename', ''),
                    'errors': [str(e)]
                })
        
        return results


# Singleton instance
nlp_pipeline = NLPPipeline()

