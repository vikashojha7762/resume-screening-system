"""
Candidate-to-Job Matching Service
Implements weighted matching with skills (50%), experience (30%), and semantic similarity (20%)
"""
import logging
import numpy as np
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.job import Job
from app.models.resume import Resume, ResumeStatus
from app.models.candidate import Candidate
import uuid
from app.services.scoring_engine import scoring_engine
from app.services.skill_extractor import skill_extractor
from app.services.experience_parser import experience_parser
from app.services.resume_parser import resume_parser
from app.services.file_service import file_service
from app.ml.embeddings import EmbeddingGenerator
from sqlalchemy.orm import Session

# Initialize embedding generator
embedding_generator = EmbeddingGenerator()

logger = logging.getLogger(__name__)


class CandidateMatcher:
    """Match candidates to jobs using weighted scoring"""
    
    def __init__(self):
        # Matching weights as specified: Skills 50%, Experience 30%, Semantic 20%
        self.weights = {
            'skills': 0.50,
            'experience': 0.30,
            'semantic': 0.20
        }
        
        # Skill synonym/normalization mapping for better matching
        self.skill_synonyms = {
            # HR/Recruitment synonyms
            'recruiting': ['talent acquisition', 'recruitment', 'hiring', 'talent sourcing'],
            'talent acquisition': ['recruiting', 'recruitment', 'hiring', 'talent sourcing'],
            'recruitment': ['recruiting', 'talent acquisition', 'hiring'],
            'hiring': ['recruiting', 'talent acquisition', 'recruitment'],
            'people management': ['team management', 'staff management', 'personnel management'],
            'employee relations': ['er', 'labor relations', 'workplace relations'],
            'performance management': ['performance review', 'performance evaluation', 'appraisal'],
            'hr policies': ['human resources policies', 'hr policy', 'workplace policies'],
            'labor law compliance': ['employment law', 'labor law', 'compliance'],
            'payroll management': ['payroll', 'payroll processing', 'salary management'],
            'compensation and benefits': ['compensation', 'benefits', 'total rewards', 'c&b'],
            'training and development': ['learning and development', 'l&d', 'training', 'employee development'],
            'conflict resolution': ['dispute resolution', 'mediation', 'conflict management'],
            'employee engagement': ['engagement', 'employee satisfaction', 'workplace culture'],
            'workforce planning': ['workforce strategy', 'talent planning', 'resource planning'],
            'hr operations': ['hr ops', 'human resources operations', 'hr administration'],
            'hr analytics': ['people analytics', 'hr metrics', 'hr data analysis'],
            'hrms tools': ['hrms', 'hris', 'human resources management system'],
            'ats tools': ['ats', 'applicant tracking system', 'recruitment software'],
            'communication skills': ['communication', 'verbal communication', 'written communication'],
            'interpersonal skills': ['people skills', 'soft skills', 'relationship building'],
            'problem solving': ['problem-solving', 'analytical thinking', 'troubleshooting'],
            'decision making': ['decision-making', 'judgment', 'critical thinking'],
            'strategic thinking': ['strategy', 'strategic planning', 'strategic vision'],
            'organizational development': ['od', 'organizational change', 'change management'],
            'change management': ['change leadership', 'transformation', 'organizational change'],
            'confidentiality': ['data privacy', 'privacy', 'confidential handling'],
            'ethical practices': ['ethics', 'professional ethics', 'integrity'],
            # Technical skills synonyms
            'python': ['python programming', 'python development'],
            'javascript': ['js', 'ecmascript'],
            'react': ['react.js', 'reactjs'],
            'postgresql': ['postgres', 'postgresql database'],
            'docker': ['docker containerization', 'containerization'],
            'kubernetes': ['k8s', 'kubernetes orchestration'],
        }
    
    def match_candidates_to_job(
        self,
        job_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Match all processed candidates to a job
        
        Args:
            job_id: Job ID to match against
            db: Database session
            
        Returns:
            Dictionary with ranked candidates and match details
        """
        try:
            # Get job
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            logger.info(f"Matching candidates to job: {job.title} (ID: {job_id})")
            
            # Extract job requirements
            job_requirements = self._extract_job_requirements(job)
            
            # Generate job embedding for semantic similarity
            job_text = f"{job.title} {job.description}"
            job_embedding = embedding_generator.generate_bert_embedding(job_text)
            
            if job_embedding is None:
                logger.warning("Failed to generate job embedding, semantic similarity will be 0")
            
            # Get all resumes (including those not fully processed)
            # Create candidates on-the-fly if they don't exist
            all_resumes = db.query(Resume).all()
            
            logger.info(f"Found {len(all_resumes)} resumes")
            
            if not all_resumes:
                return {
                    'job_id': str(job_id),
                    'job_title': job.title,
                    'candidates_matched': 0,
                    'ranked_candidates': [],
                    'matching_weights': self.weights,
                    'message': 'No resumes found. Please upload resumes first.'
                }
            
            # Match each resume
            match_results = []
            
            for resume in all_resumes:
                # Get or create candidate for this resume
                candidate = db.query(Candidate).filter(Candidate.resume_id == resume.id).first()
                if not candidate:
                    # Create candidate on-the-fly
                    import uuid
                    anonymized_id = f"CAND-{uuid.uuid4().hex[:8].upper()}"
                    candidate = Candidate(
                        anonymized_id=anonymized_id,
                        resume_id=resume.id,
                        masked_data_json={}
                    )
                    db.add(candidate)
                    db.commit()
                    db.refresh(candidate)
                    logger.info(f"Created candidate {candidate.id} for resume {resume.id}")
                
                # ALWAYS get resume_text from multiple sources (parsed_data_json OR file_path)
                resume_data = resume.parsed_data_json or {}
                
                # Try to get resume_text from parsed_data_json (multiple possible keys)
                resume_text = (
                    resume_data.get('raw_text', '') or
                    resume_data.get('parsed_text', '') or
                    resume_data.get('extracted_text', '') or
                    ''
                )
                
                # If no text in parsed_data, read from file_path
                if not resume_text or len(resume_text.strip()) < 50:
                    logger.warning(f"Resume {resume.id} has no/minimal text in parsed_data_json, reading from file_path: {resume.file_path}")
                    try:
                        # Read file content from file_path
                        file_content = file_service.read_file(resume.file_path)
                        if file_content:
                            # Parse the file to extract text
                            file_type = resume.file_type or (resume.file_name.split('.')[-1] if '.' in resume.file_name else 'pdf')
                            parsed_result = resume_parser.parse(file_content, file_type, resume.file_name)
                            resume_text = parsed_result.get('raw_text', '') or parsed_result.get('parsed_text', '') or ''
                            logger.info(f"Extracted {len(resume_text)} characters from file_path")
                        else:
                            logger.error(f"Failed to read file from file_path: {resume.file_path}")
                            resume_text = resume.file_name or ''  # Last resort fallback
                    except Exception as e:
                        logger.error(f"Error reading/parsing file from file_path {resume.file_path}: {str(e)}", exc_info=True)
                        resume_text = resume.file_name or ''  # Last resort fallback
                
                logger.info(f"Processing resume {resume.id}: resume_text length={len(resume_text)}")
                
                # Validate we have sufficient text
                if not resume_text or len(resume_text.strip()) < 50:
                    logger.error(f"Resume {resume.id} has insufficient text ({len(resume_text)} chars), skipping detailed matching")
                    # Use minimal matching with filename only
                    resume_text = resume.file_name or ''
                
                # Extract skills directly from resume_text
                logger.info(f"📄 Resume {resume.id}: Extracting skills from resume_text (length: {len(resume_text)} chars)")
                skills_data = {}
                extracted_skills = []
                
                if resume_text and len(resume_text) > 50:
                    try:
                        # Method 1: Use skill_extractor (spaCy-based)
                        skills_data = skill_extractor.extract_skills(resume_text)
                        # Normalize skill_extractor output - it returns {'skills': [...], 'skill_scores': {...}, ...}
                        if isinstance(skills_data, dict):
                            # Primary: 'skills' key (list of skill names)
                            extracted_skills = skills_data.get('skills', [])
                            
                            # Fallback: if 'skills' is empty, try 'categorized_skills' (flatten all categories)
                            if not extracted_skills:
                                categorized = skills_data.get('categorized_skills', {})
                                if isinstance(categorized, dict):
                                    for category_skills in categorized.values():
                                        if isinstance(category_skills, list):
                                            extracted_skills.extend(category_skills)
                            
                            # Ensure we have a list
                            if not isinstance(extracted_skills, list):
                                extracted_skills = []
                    except Exception as e:
                        logger.error(f"Error extracting skills with skill_extractor: {str(e)}", exc_info=True)
                        skills_data = {}
                        extracted_skills = []
                
                # Method 2: Direct text matching fallback for HR terms (if skill_extractor returned empty)
                if not extracted_skills and resume_text:
                    logger.info(f"⚠️  skill_extractor returned empty, using direct text matching fallback")
                    hr_terms = [
                        'recruitment', 'recruiting', 'talent acquisition', 'hiring', 'talent sourcing',
                        'employee relations', 'er', 'labor relations', 'workplace relations',
                        'performance management', 'performance review', 'performance evaluation',
                        'hr policies', 'human resources policies', 'workplace policies',
                        'payroll', 'payroll management', 'payroll processing',
                        'compensation', 'benefits', 'compensation and benefits', 'total rewards',
                        'training', 'employee development', 'learning and development', 'l&d',
                        'conflict resolution', 'dispute resolution', 'mediation',
                        'employee engagement', 'workplace culture',
                        'workforce planning', 'talent planning',
                        'hr operations', 'hr ops', 'hr administration',
                        'hr analytics', 'people analytics', 'hr metrics',
                        'hrms', 'hris', 'human resources management system',
                        'ats', 'applicant tracking system',
                        'compliance', 'labor law compliance', 'employment law',
                        'onboarding', 'offboarding', 'talent management',
                        'succession planning', 'organizational development', 'od'
                    ]
                    resume_text_lower = resume_text.lower()
                    for term in hr_terms:
                        if term in resume_text_lower:
                            extracted_skills.append(term)
                    logger.info(f"✅ Direct text matching found {len(extracted_skills)} HR skills")
                
                logger.info(f"✅ FINAL: Extracted {len(extracted_skills)} skills from resume: {extracted_skills[:15]}")
                
                # Extract experience directly from resume_text
                logger.info(f"📄 Resume {resume.id}: Extracting experience from resume_text (length: {len(resume_text)} chars)")
                experience_data = {}
                total_experience_years = 0.0
                
                if resume_text and len(resume_text) > 50:
                    try:
                        # Method 1: Use experience_parser
                        experience_data = experience_parser.extract_experience(resume_text)
                        if isinstance(experience_data, dict):
                            # Primary: 'total_experience_years' key
                            total_experience_years = experience_data.get('total_experience_years', 0.0)
                            
                            # Fallback: compute from experiences array if total_experience_years is missing/zero
                            if total_experience_years == 0.0 and 'experiences' in experience_data:
                                experiences = experience_data.get('experiences', [])
                                logger.debug(f"Computing total_experience_years from {len(experiences)} experiences")
                                
                                total_months = 0
                                for exp in experiences:
                                    if isinstance(exp, dict):
                                        # Try duration_months first
                                        months = exp.get('duration_months', 0) or exp.get('months', 0)
                                        if months:
                                            total_months += int(months)
                                        else:
                                            # Try duration_years
                                            years = exp.get('duration_years', 0) or exp.get('years', 0)
                                            if years:
                                                total_months += float(years) * 12
                                            else:
                                                # Calculate from dates
                                                start_date = exp.get('start_date') or exp.get('start')
                                                end_date = exp.get('end_date') or exp.get('end') or 'present'
                                                if start_date:
                                                    try:
                                                        from dateparser import parse as parse_date
                                                        from datetime import datetime
                                                        start = parse_date(str(start_date))
                                                        if start:
                                                            if end_date and end_date.lower() not in ['present', 'current', 'now']:
                                                                end = parse_date(str(end_date))
                                                            else:
                                                                end = datetime.now()
                                                            if end:
                                                                delta = end - start
                                                                months = int(delta.days / 30.44)
                                                                total_months += months
                                                    except Exception:
                                                        pass
                                
                                total_experience_years = round(total_months / 12.0, 1)
                                logger.debug(f"Computed total_experience_years: {total_experience_years} from experiences array")
                                
                                # Update experience_data with computed value
                                experience_data['total_experience_years'] = total_experience_years
                    except Exception as e:
                        logger.error(f"Error extracting experience with experience_parser: {str(e)}", exc_info=True)
                        experience_data = {}
                        total_experience_years = 0.0
                
                # Method 2: Comprehensive date-range based extraction (if parser returned 0)
                if total_experience_years == 0.0 and resume_text:
                    logger.info(f"⚠️  experience_parser returned 0 years, using comprehensive date-range extraction")
                    extracted_experience = self._extract_experience_from_text(resume_text)
                    if extracted_experience and extracted_experience.get('total_experience_years', 0) > 0:
                        total_experience_years = extracted_experience['total_experience_years']
                        # Update experience_data with extracted information
                        experience_data.update(extracted_experience)
                        logger.info(f"✅ Date-range extraction found {total_experience_years} years from {len(extracted_experience.get('experiences', []))} positions")
                
                # Method 3: Text fallback for "X years of experience" patterns (if still 0)
                if total_experience_years == 0.0 and resume_text:
                    logger.info(f"⚠️  No date ranges found, using text pattern fallback")
                    total_experience_years = self._extract_experience_from_text_patterns(resume_text)
                    if total_experience_years > 0:
                        logger.info(f"✅ Text pattern fallback found {total_experience_years} years")
                        # Update experience_data
                        if not experience_data:
                            experience_data = {}
                        experience_data['total_experience_years'] = total_experience_years
                
                # HARD VALIDATION: If resume has substantial text and dates but 0 experience
                if len(resume_text) > 500 and total_experience_years == 0.0:
                    # Check if dates exist in text
                    date_patterns = [
                        r'\d{4}\s*[-–]\s*(?:present|\d{4})',
                        r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}',
                        r'\d{1,2}[/-]\d{4}'
                    ]
                    has_dates = any(re.search(pattern, resume_text, re.IGNORECASE) for pattern in date_patterns)
                    if has_dates:
                        logger.error(f"❌ VALIDATION ERROR: Resume has {len(resume_text)} chars and contains dates but experience_years = 0. Extraction may have failed.")
                
                logger.info(f"✅ FINAL: Extracted {total_experience_years} years of experience from resume")
                
                # Build resume_data structure with extracted values
                resume_data_for_matching = {
                    'raw_text': resume_text,
                    'skills': skills_data,  # Full skills data from extractor
                    'experience': experience_data,  # Full experience data from parser
                    'contact_info': resume_data.get('contact_info', {})
                }
                
                # Calculate skill match score (50%)
                skill_score, skill_details = self._calculate_skill_match(
                    resume_data_for_matching, job_requirements, resume_text
                )
                logger.info(f"📊 Resume {resume.id} SKILL SCORE: {skill_score:.2%} ({len(skill_details.get('matched_skills', []))}/{len(job_requirements.get('required_skills', [])) + len(job_requirements.get('preferred_skills', []))} matched)")
                
                # Calculate experience match score (30%)
                experience_score, experience_details = self._calculate_experience_match(
                    resume_data_for_matching, job_requirements
                )
                logger.info(f"📊 Resume {resume.id} EXPERIENCE SCORE: {experience_score:.2%} (Resume: {experience_details.get('resume_years', 0):.1f} years, Required: {experience_details.get('required_years', 0):.1f} years)")
                
                # Calculate semantic similarity score (20%) - always from resume_text
                semantic_score = self._calculate_semantic_similarity(
                    resume, job_embedding, resume_text
                )
                # Ensure semantic_score has a safe fallback (default to 0.4 for related content)
                if semantic_score is None:
                    semantic_score = 0.4  # Minimum for related content
                elif semantic_score < 0.4:
                    semantic_score = 0.4  # Minimum baseline for HR-related resumes
                logger.info(f"📊 Resume {resume.id} SEMANTIC SCORE: {semantic_score:.2%}")
                
                # Calculate final weighted score (Skills: 50%, Experience: 30%, Semantic: 20%)
                final_score = (
                    skill_score * self.weights['skills'] +
                    experience_score * self.weights['experience'] +
                    semantic_score * self.weights['semantic']
                ) * 100  # Convert to percentage
                
                # Ensure score is between 0-100
                final_score = max(0.0, min(100.0, final_score))
                
                logger.info(f"🎯 Resume {resume.id} FINAL SCORE: {final_score:.2f}% (Skills: {skill_score*100:.1f}% × 50% = {skill_score*self.weights['skills']*100:.1f}%, Experience: {experience_score*100:.1f}% × 30% = {experience_score*self.weights['experience']*100:.1f}%, Semantic: {semantic_score*100:.1f}% × 20% = {semantic_score*self.weights['semantic']*100:.1f}%)")
                
                # Extract matched and missing skills
                matched_skills = skill_details.get('matched_skills', [])
                missing_skills = skill_details.get('missing_skills', [])
                
                match_results.append({
                    'candidate_id': str(candidate.id),
                    'anonymized_id': candidate.anonymized_id,
                    'resume_id': str(resume.id),
                    'resume_file_name': resume.file_name,
                    'final_score': round(final_score, 2),
                    'component_scores': {
                        'skills': round(skill_score * 100, 2),
                        'experience': round(experience_score * 100, 2),
                        'semantic_similarity': round(float(semantic_score or 0.0) * 100, 2)
                    },
                    'matched_skills': matched_skills,
                    'missing_skills': missing_skills,
                    'experience_summary': experience_details.get('summary', ''),
                    'candidate_name': self._extract_candidate_name(resume_data)
                })
            
            # Sort by final score (descending)
            match_results.sort(key=lambda x: x['final_score'], reverse=True)
            
            # Add rank
            for idx, result in enumerate(match_results, start=1):
                result['rank'] = idx
            
            logger.info(f"Matched {len(match_results)} candidates to job {job_id}")
            
            return {
                'job_id': str(job_id),
                'job_title': job.title,
                'candidates_matched': len(match_results),
                'ranked_candidates': match_results,
                'matching_weights': self.weights
            }
            
        except Exception as e:
            logger.error(f"Error matching candidates to job: {str(e)}", exc_info=True)
            raise
    
    def _extract_job_requirements(self, job: Job) -> Dict[str, Any]:
        """Extract requirements from job description"""
        requirements = job.requirements_json or {}
        
        # Extract from requirements_json if available
        required_skills = requirements.get('required_skills', [])
        preferred_skills = requirements.get('preferred_skills', [])
        required_experience = requirements.get('required_experience_years', 0)
        preferred_experience = requirements.get('preferred_experience_years', 0)
        
        # If not in requirements_json, try to extract from description
        if not required_skills and not preferred_skills:
            logger.info(f"Job {job.id} has no skills in requirements_json, extracting from description")
            # Extract skills from job description using skill_extractor
            job_text = f"{job.title} {job.description}"
            if job_text and len(job_text.strip()) > 20:
                try:
                    skills_data = skill_extractor.extract_skills(job_text)
                    if isinstance(skills_data, dict):
                        extracted_skills = skills_data.get('skills', [])
                        if extracted_skills:
                            # Use extracted skills as required_skills
                            required_skills = extracted_skills[:10]  # Top 10 skills
                            logger.info(f"Extracted {len(required_skills)} skills from job description: {required_skills[:5]}")
                except Exception as e:
                    logger.warning(f"Error extracting skills from job description: {str(e)}")
        
        return {
            'required_skills': required_skills if isinstance(required_skills, list) else [],
            'preferred_skills': preferred_skills if isinstance(preferred_skills, list) else [],
            'required_experience_years': float(required_experience) if required_experience else 0.0,
            'preferred_experience_years': float(preferred_experience) if preferred_experience else 0.0
        }
    
    def _normalize_skill(self, skill: str) -> str:
        """
        Normalize skill name for comparison
        ENHANCED: Aggressive HR skill normalization for better matching
        """
        if not skill:
            return ''
        # Convert to lowercase and strip
        normalized = skill.lower().strip()
        
        # Aggressive HR skill normalization
        # "human resource management" → "hr management"
        normalized = re.sub(r'\bhuman\s+resources?\b', 'hr', normalized)
        normalized = re.sub(r'\bhuman\s+resource\b', 'hr', normalized)
        
        # "people operations" → "people management"
        normalized = re.sub(r'\bpeople\s+operations\b', 'people management', normalized)
        
        # "employee lifecycle" → "employee relations"
        normalized = re.sub(r'\bemployee\s+lifecycle\b', 'employee relations', normalized)
        
        # Normalize management variations
        normalized = normalized.replace('management', 'mgmt').replace('mgmt', 'management')
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Return normalized version
        return normalized
    
    def _get_skill_variants(self, skill: str) -> List[str]:
        """Get all variants/synonyms of a skill for matching"""
        normalized = self._normalize_skill(skill)
        variants = {normalized}
        
        # Add from synonym mapping
        if normalized in self.skill_synonyms:
            for synonym in self.skill_synonyms[normalized]:
                variants.add(self._normalize_skill(synonym))
        
        # Also check reverse mapping (if any synonym matches, include the main skill)
        for main_skill, synonyms in self.skill_synonyms.items():
            if normalized in [self._normalize_skill(s) for s in synonyms]:
                variants.add(self._normalize_skill(main_skill))
        
        return list(variants)
    
    def _match_skill(self, job_skill: str, resume_skills: List[str]) -> bool:
        """
        Check if job skill matches any resume skill (with synonyms and partial matching)
        ENHANCED: Uses partial word overlap (≥60% words) for multi-word skills
        """
        job_variants = self._get_skill_variants(job_skill)
        normalized_resume_skills = [self._normalize_skill(s) for s in resume_skills]
        
        # Check exact match
        for variant in job_variants:
            if variant in normalized_resume_skills:
                return True
        
        # Check partial match (if job skill contains resume skill or vice versa)
        for variant in job_variants:
            for resume_skill in normalized_resume_skills:
                # Partial match: one contains the other (minimum 3 characters)
                if len(variant) >= 3 and len(resume_skill) >= 3:
                    if variant in resume_skill or resume_skill in variant:
                        return True
        
        # ENHANCED: Check partial word overlap for multi-word skills (≥60% words must overlap)
        # Example: "performance appraisal" matches "performance management" (1/2 words = 50%, but we check both ways)
        for variant in job_variants:
            variant_words = set(variant.split())
            if len(variant_words) >= 2:  # Only for multi-word skills
                for resume_skill in normalized_resume_skills:
                    resume_words = set(resume_skill.split())
                    if len(resume_words) >= 2:  # Only for multi-word skills
                        # Calculate word overlap percentage
                        common_words = variant_words.intersection(resume_words)
                        if common_words:
                            # Check overlap in both directions (≥60% threshold)
                            overlap_variant = len(common_words) / len(variant_words) if variant_words else 0
                            overlap_resume = len(common_words) / len(resume_words) if resume_words else 0
                            
                            # If ≥60% words overlap in either direction, consider it a match
                            if overlap_variant >= 0.6 or overlap_resume >= 0.6:
                                logger.debug(f"Matched '{job_skill}' with '{resume_skill}' via word overlap ({len(common_words)}/{len(variant_words)} or {len(common_words)}/{len(resume_words)} words)")
                                return True
        
        return False
    
    def _extract_all_resume_skills(self, resume_data: Dict[str, Any]) -> List[str]:
        """
        Extract skills from skills_data (already extracted from raw_text)
        ENHANCED: Extracts from multiple sections (SKILLS, RESPONSIBILITIES, EXPERIENCE bullet points)
        """
        all_skills = set()
        raw_text = resume_data.get('raw_text', '')
        
        # Method 1: Get from skills dict (should be populated by skill_extractor.extract_skills())
        skills_data = resume_data.get('skills', {})
        if isinstance(skills_data, dict):
            # Primary key: 'skills' (list) - this is what skill_extractor returns
            skills_list = skills_data.get('skills', [])
            if skills_list:
                all_skills.update([s for s in skills_list if s and isinstance(s, str)])
                logger.debug(f"Found {len(skills_list)} skills in 'skills' key")
            
            # Also check 'extracted' (legacy/alternative format)
            extracted = skills_data.get('extracted', [])
            if extracted:
                all_skills.update([s for s in extracted if s and isinstance(s, str)])
                logger.debug(f"Found {len(extracted)} skills in 'extracted' key")
            
            # Extract from categorized_skills (flatten all categories)
            categorized = skills_data.get('categorized_skills', {})
            if isinstance(categorized, dict):
                for category_skills in categorized.values():
                    if isinstance(category_skills, list):
                        all_skills.update([s for s in category_skills if s and isinstance(s, str)])
                logger.debug(f"Found skills in {len(categorized)} categories")
            
            # Check other possible keys
            all_skills_list = skills_data.get('all_skills', [])
            if all_skills_list:
                all_skills.update([s for s in all_skills_list if s and isinstance(s, str)])
        
        elif isinstance(skills_data, list):
            # Skills data is directly a list
            all_skills.update([s for s in skills_data if s and isinstance(s, str)])
        
        # Method 2: Extract from SKILLS section in raw_text
        if raw_text and len(raw_text) > 50:
            import re
            # Look for skills section (multiple patterns)
            skills_section_patterns = [
                r'(?:skills?|technical\s+skills?|competencies?|expertise|core\s+skills?)[:;]?\s*\n(.*?)(?:\n\n|\n[A-Z]|$)',
                r'(?:key\s+skills?|professional\s+skills?)[:;]?\s*\n(.*?)(?:\n\n|\n[A-Z]|$)',
            ]
            for pattern in skills_section_patterns:
                skills_section_match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)
                if skills_section_match:
                    skills_text = skills_section_match.group(1)
                    # Split by common delimiters
                    extracted_skills = re.split(r'[,;•\-\n]', skills_text)
                    all_skills.update([s.strip() for s in extracted_skills if s.strip() and len(s.strip()) > 2])
                    logger.debug(f"Extracted {len(extracted_skills)} skills from SKILLS section")
                    break
        
        # Method 3: Extract from RESPONSIBILITIES section (often contains skills)
        if raw_text and len(raw_text) > 50:
            responsibilities_match = re.search(
                r'(?:responsibilities?|key\s+responsibilities?|duties?)[:;]?\s*\n(.*?)(?:\n\n|\n[A-Z]|$)',
                raw_text,
                re.IGNORECASE | re.DOTALL
            )
            if responsibilities_match:
                responsibilities_text = responsibilities_match.group(1)
                # Extract skills mentioned in responsibilities (look for common skill patterns)
                # HR skills, technical terms, etc.
                skill_keywords = [
                    r'\b(?:managed|handled|responsible\s+for|oversaw|led|coordinated|developed|implemented)\s+([a-z\s]+?)(?:\.|,|\n)',
                ]
                for pattern in skill_keywords:
                    matches = re.finditer(pattern, responsibilities_text.lower())
                    for match in matches:
                        potential_skill = match.group(1).strip()
                        if len(potential_skill) > 3 and len(potential_skill) < 50:
                            all_skills.add(potential_skill)
                logger.debug(f"Extracted skills from RESPONSIBILITIES section")
        
        # Method 4: Extract from EXPERIENCE bullet points (often contain skills)
        if raw_text and len(raw_text) > 50:
            # Look for bullet points in experience section
            experience_match = re.search(
                r'(?:experience|work\s+history|employment)[:;]?\s*\n(.*?)(?:\n\n|\n[A-Z]{2,}|$)',
                raw_text,
                re.IGNORECASE | re.DOTALL
            )
            if experience_match:
                experience_text = experience_match.group(1)
                # Extract bullet points (lines starting with •, -, *, or numbered)
                bullet_points = re.findall(r'[•\-\*]\s*(.+?)(?:\n|$)', experience_text, re.IGNORECASE | re.MULTILINE)
                for bullet in bullet_points:
                    # Look for skill-related phrases
                    # Common patterns: "worked with X", "experienced in X", "proficient in X"
                    skill_patterns = [
                        r'(?:worked\s+with|experienced\s+in|proficient\s+in|skilled\s+in|expertise\s+in|knowledge\s+of)\s+([a-z\s]+?)(?:\.|,|\n|$)',
                        r'(?:using|utilizing|applying)\s+([a-z\s]+?)(?:\.|,|\n|$)',
                    ]
                    for pattern in skill_patterns:
                        matches = re.finditer(pattern, bullet.lower())
                        for match in matches:
                            potential_skill = match.group(1).strip()
                            if len(potential_skill) > 3 and len(potential_skill) < 50:
                                all_skills.add(potential_skill)
                logger.debug(f"Extracted skills from EXPERIENCE bullet points")
        
        # Normalize all skills
        normalized_skills = [self._normalize_skill(s) for s in all_skills if s]
        # Remove None values and duplicates
        result = list(set([s for s in normalized_skills if s]))
        logger.debug(f"Final normalized skills count: {len(result)} (extracted from multiple sections)")
        return result
    
    def _calculate_skill_match(
        self,
        resume_data: Dict[str, Any],
        job_requirements: Dict[str, Any],
        resume_text: str = ''
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate skill match score (0-1) with synonym and partial matching"""
        try:
            # Extract skills from ALL available sources
            resume_skills = self._extract_all_resume_skills(resume_data)
            
            logger.debug(f"Extracted {len(resume_skills)} skills from resume: {resume_skills[:10]}")
            
            required_skills = [s for s in job_requirements.get('required_skills', []) if s and isinstance(s, str)]
            preferred_skills = [s for s in job_requirements.get('preferred_skills', []) if s and isinstance(s, str)]
            
            # CRITICAL FALLBACK: If no resume_skills found, match JD skills directly against resume_text
            if not resume_skills and resume_text and (required_skills or preferred_skills):
                logger.warning("⚠️  No skills extracted from resume, using direct text matching fallback")
                all_job_skills = required_skills + preferred_skills
                resume_text_lower = resume_text.lower()
                for job_skill in all_job_skills:
                    if job_skill and isinstance(job_skill, str):
                        # Case-insensitive matching
                        if job_skill.lower() in resume_text_lower:
                            resume_skills.append(job_skill.lower())
                        # Also check synonyms
                        job_variants = self._get_skill_variants(job_skill)
                        for variant in job_variants:
                            if variant in resume_text_lower:
                                resume_skills.append(variant)
                                break
                logger.info(f"✅ Direct text matching found {len(resume_skills)} skills: {resume_skills[:10]}")
            
            if not resume_skills:
                logger.warning("⚠️  No skills found in resume data, skill score will be 0")
            
            # Calculate matches using improved matching
            matched_required = []
            matched_preferred = []
            
            for req_skill in required_skills:
                if self._match_skill(req_skill, resume_skills):
                    matched_required.append(req_skill)
            
            for pref_skill in preferred_skills:
                if self._match_skill(pref_skill, resume_skills):
                    matched_preferred.append(pref_skill)
            
            missing_required = [s for s in required_skills if s not in matched_required]
            missing_preferred = [s for s in preferred_skills if s not in matched_preferred]
            
            # Calculate score
            # Required skills are mandatory (weight: 0.7)
            # Preferred skills are bonus (weight: 0.3)
            required_score = len(matched_required) / len(required_skills) if required_skills else 1.0
            preferred_score = len(matched_preferred) / len(preferred_skills) if preferred_skills else 1.0
            
            # If no skills specified, give full score
            if not required_skills and not preferred_skills:
                skill_score = 1.0
                logger.debug("No job skills specified, giving full skill score")
            else:
                skill_score = (required_score * 0.7) + (preferred_score * 0.3)
                logger.info(f"🔍 Skill matching details: required={required_score:.2%} ({len(matched_required)}/{len(required_skills)} matched), preferred={preferred_score:.2%} ({len(matched_preferred)}/{len(preferred_skills)} matched), final={skill_score:.2%}")
            
            return skill_score, {
                'matched_skills': list(set(matched_required + matched_preferred)),
                'missing_skills': list(set(missing_required + missing_preferred)),
                'required_matched': len(matched_required),
                'required_total': len(required_skills),
                'preferred_matched': len(matched_preferred),
                'preferred_total': len(preferred_skills)
            }
            
        except Exception as e:
            logger.error(f"Error calculating skill match: {str(e)}", exc_info=True)
            return 0.0, {'matched_skills': [], 'missing_skills': []}
    
    def _is_internship_position(self, position: Dict[str, Any]) -> bool:
        """
        Detect if a position is an internship (should NOT count toward required experience)
        Checks job title, description, and keywords
        ENHANCED: Also detects student projects and academic work
        """
        if not isinstance(position, dict):
            return False
        
        # Check job title for internship/academic keywords
        title = str(position.get('title', '') or position.get('job_title', '') or '').lower()
        # Expanded keywords: includes "student", "project" for academic work
        internship_keywords = ['intern', 'internship', 'trainee', 'virtual internship', 'co-op', 'coop', 
                               'student', 'academic', 'university project', 'college project', 'project']
        
        # Check if title contains internship keywords
        has_internship_keyword = any(keyword in title for keyword in internship_keywords)
        
        # CRITICAL: Check for professional role indicators
        # If title contains professional indicators, it's NOT an internship
        professional_indicators = ['manager', 'executive', 'lead', 'officer', 'specialist', 
                                  'director', 'coordinator', 'analyst', 'engineer', 'developer', 
                                  'consultant', 'supervisor', 'head of']
        has_professional_indicator = any(indicator in title for indicator in professional_indicators)
        
        # If has professional indicator, it's NOT an internship
        if has_professional_indicator:
            return False
        
        # If has internship keyword, it's an internship
        if has_internship_keyword:
            return True
        
        # Check description/company for internship indicators
        description = str(position.get('description', '') or position.get('company', '') or '').lower()
        if any(keyword in description for keyword in internship_keywords):
            # But check if description also has professional indicators
            if not any(indicator in description for indicator in professional_indicators):
                return True
        
        return False
    
    def _calculate_experience_match(
        self,
        resume_data: Dict[str, Any],
        job_requirements: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate experience match score (0-1) with improved extraction
        CRITICAL: Internships are excluded from experience calculation
        """
        try:
            # Get resume experience
            experience_data = resume_data.get('experience', {})
            
            # Extract total years of experience (EXCLUDING internships)
            total_years = 0.0
            internship_count = 0
            professional_count = 0
            
            if isinstance(experience_data, dict):
                # Method 1: Try direct total years keys (highest priority - this is what experience_parser returns)
                raw_total_years = float(experience_data.get('total_experience_years', 0) or 
                                  experience_data.get('total_years', 0) or 
                                  experience_data.get('years', 0) or
                                  experience_data.get('experience_years', 0) or 0)
                
                logger.debug(f"Initial total_years from direct keys: {raw_total_years}")
                
                # Method 2: Calculate from experiences array (filtering out internships)
                if 'experiences' in experience_data:
                    experiences = experience_data.get('experiences', [])
                    logger.debug(f"Analyzing {len(experiences)} experiences for internship detection")
                    
                    for exp in experiences:
                        if isinstance(exp, dict):
                            # Check if this is an internship
                            if self._is_internship_position(exp):
                                internship_count += 1
                                logger.debug(f"Excluding internship: {exp.get('title', 'N/A')}")
                                continue  # Skip internships
                            
                            # Count as professional experience
                            professional_count += 1
                            
                            # Try duration_years first
                            duration_years = exp.get('duration_years', 0) or exp.get('years', 0)
                            if duration_years:
                                total_years += float(duration_years)
                                logger.debug(f"Added {duration_years} years from professional position: {exp.get('title', 'N/A')}")
                            else:
                                # Try duration_months
                                months = exp.get('duration_months', 0) or exp.get('months', 0)
                                if months:
                                    total_years += float(months) / 12.0
                                    logger.debug(f"Added {months} months ({months/12.0:.2f} years) from professional position")
                                else:
                                    # Calculate from start/end dates
                                    start_date = exp.get('start_date') or exp.get('start')
                                    end_date = exp.get('end_date') or exp.get('end') or 'present'
                                    
                                    if start_date:
                                        try:
                                            from dateparser import parse as parse_date
                                            from datetime import datetime
                                            
                                            # Parse start date
                                            start = parse_date(str(start_date))
                                            if start:
                                                # Parse end date (or use current if 'present')
                                                if end_date and end_date.lower() not in ['present', 'current', 'now']:
                                                    end = parse_date(str(end_date))
                                                else:
                                                    end = datetime.now()
                                                
                                                if end:
                                                    delta = end - start
                                                    years = delta.days / 365.25
                                                    if years > 0:
                                                        total_years += years
                                                        logger.debug(f"Calculated {years:.2f} years from dates: {start_date} to {end_date}")
                                        except Exception as e:
                                            logger.warning(f"Error parsing dates: {start_date} to {end_date}: {str(e)}")
                                            pass
                
                # If we calculated from experiences array, use that (it excludes internships)
                # Otherwise, use raw_total_years but check if it's internship-only
                if total_years == 0 and raw_total_years > 0:
                    # Check if all experiences are internships
                    if 'experiences' in experience_data:
                        experiences = experience_data.get('experiences', [])
                        all_internships = all(self._is_internship_position(exp) for exp in experiences if isinstance(exp, dict))
                        if all_internships and len(experiences) > 0:
                            logger.warning(f"⚠️  All {len(experiences)} positions are internships - setting total_years = 0")
                            total_years = 0.0
                        else:
                            # Use raw_total_years if we have professional experience
                            total_years = raw_total_years
                    else:
                        # No experiences array, use raw_total_years
                        total_years = raw_total_years
                elif total_years > 0:
                    # We calculated from experiences array (internships excluded)
                    logger.debug(f"Using calculated total_years from experiences array (internships excluded): {total_years}")
                
                # Check positions array (legacy format) for internships
                if 'positions' in experience_data:
                    positions = experience_data.get('positions', [])
                    for pos in positions:
                        if isinstance(pos, dict) and self._is_internship_position(pos):
                            internship_count += 1
                            logger.debug(f"Excluding internship from positions array: {pos.get('title', 'N/A')}")
                
                # Method 3: Calculate from positions array (legacy format)
                if total_years == 0 and 'positions' in experience_data:
                    positions = experience_data.get('positions', [])
                    for pos in positions:
                        if isinstance(pos, dict):
                            # Try multiple duration fields
                            duration = (pos.get('duration_years', 0) or 
                                      pos.get('years', 0) or
                                      pos.get('duration', 0) or 0)
                            if duration:
                                total_years += float(duration)
                            else:
                                # Try to calculate from start/end dates
                                start_date = pos.get('start_date') or pos.get('start')
                                end_date = pos.get('end_date') or pos.get('end') or 'present'
                                if start_date:
                                    try:
                                        from dateparser import parse as parse_date
                                        start = parse_date(str(start_date))
                                        end = parse_date(str(end_date)) if end_date and end_date.lower() != 'present' else None
                                        if start:
                                            if end:
                                                delta = end - start
                                            else:
                                                from datetime import datetime
                                                delta = datetime.now() - start
                                            years = delta.days / 365.25
                                            if years > 0:
                                                total_years += years
                                    except Exception:
                                        pass
                
                # Method 4: Extract from raw text or summary (last resort)
                if total_years == 0:
                    # Look for experience summary or text
                    summary = experience_data.get('summary', '') or experience_data.get('text', '')
                    if not summary:
                        # Try to extract from raw_text in resume_data
                        raw_text = resume_data.get('raw_text', '')
                        if raw_text:
                            # Look for experience section
                            import re
                            exp_section_match = re.search(r'(?:experience|work history|employment)[:\s]*\n(.*?)(?:\n\n[A-Z]|$)', raw_text, re.IGNORECASE | re.DOTALL)
                            if exp_section_match:
                                summary = exp_section_match.group(1)
                    
                    if summary:
                        import re
                        # Look for patterns like "8 years", "8+ years", "8-10 years"
                        patterns = [
                            r'(\d+(?:\.\d+)?)\s*\+\s*years?',
                            r'(\d+(?:\.\d+)?)\s*-\s*\d+\s*years?',
                            r'(\d+(?:\.\d+)?)\s*years?\s*of\s*experience',
                            r'(\d+(?:\.\d+)?)\s*years?',
                        ]
                        for pattern in patterns:
                            matches = re.findall(pattern, summary.lower())
                            if matches:
                                try:
                                    total_years = max(total_years, float(matches[0]))
                                    break
                                except ValueError:
                                    pass
            
            # CRITICAL: Check if experience is internship-only or academic-only
            # If only internships/student projects found, set total_years = 0
            if total_years > 0 and internship_count > 0 and professional_count == 0:
                logger.warning(f"⚠️  Only internships/student work detected ({internship_count} positions) - setting total_years = 0")
                total_years = 0.0
            
            # Also check raw_text for internship-only/academic-only indicators
            raw_text = resume_data.get('raw_text', '')
            if total_years > 0 and raw_text:
                raw_text_lower = raw_text.lower()
                # Expanded keywords: includes "student", "project" for academic work
                internship_keywords = ['intern', 'internship', 'trainee', 'virtual internship', 
                                      'student', 'academic project', 'university project', 'college project']
                # If resume mentions only internships/student work and no professional roles
                has_internship_mentions = any(keyword in raw_text_lower for keyword in internship_keywords)
                # Check for professional role indicators (more comprehensive)
                professional_indicators = ['manager', 'director', 'executive', 'specialist', 'coordinator', 
                                          'analyst', 'engineer', 'developer', 'consultant', 'lead', 'officer',
                                          'supervisor', 'head of', 'senior', 'principal']
                has_professional_mentions = any(indicator in raw_text_lower for indicator in professional_indicators)
                
                # If resume has internship mentions but NO professional indicators AND total_years is low
                # Treat as non-professional experience
                if has_internship_mentions and not has_professional_mentions and total_years < 2.0:
                    # Likely internship-only or academic-only resume
                    logger.warning(f"⚠️  Resume appears internship/academic-only (no professional roles) - setting total_years = 0")
                    total_years = 0.0
            
            logger.info(f"Final calculated total_years: {total_years} (Professional: {professional_count}, Internships excluded: {internship_count})")
            
            # Get job requirements
            required_years = job_requirements.get('required_experience_years', 0.0)
            preferred_years = job_requirements.get('preferred_experience_years', 0.0)
            
            # Calculate score
            # CRITICAL: If total_years == 0, experience_score MUST be 0.0 (not 1.0)
            # REMOVED: Default 1.0 when required_years == 0 if total_years == 0
            if total_years == 0.0:
                experience_score = 0.0
                if internship_count > 0:
                    summary = f"Internship experience only (not counted)"
                else:
                    summary = "No professional experience detected"
                logger.info(f"⚠️  No professional experience: {summary}")
            elif required_years == 0 and preferred_years == 0:
                # No experience requirement, but candidate has professional experience
                # Only give 1.0 if candidate actually has experience
                if total_years > 0:
                    experience_score = 1.0
                    summary = f"No specific experience requirement ({total_years:.1f} years available)"
                else:
                    # No requirement AND no experience = neutral score (0.5)
                    experience_score = 0.5
                    summary = "No experience requirement specified"
            elif total_years >= required_years:
                # Meets or exceeds requirement - ALWAYS give 1.0 if meets requirement
                experience_score = 1.0
                if preferred_years > required_years:
                    if total_years >= preferred_years:
                        summary = f"Exceeds preferred experience ({total_years:.1f} years)"
                    else:
                        summary = f"Meets required, approaching preferred ({total_years:.1f} years)"
                else:
                    summary = f"Meets experience requirement ({total_years:.1f} years)"
                logger.info(f"✅ Experience requirement met: {total_years:.1f} >= {required_years:.1f} years")
            else:
                # Below requirement
                if required_years > 0:
                    experience_score = max(0.0, total_years / required_years)
                    summary = f"Below required experience ({total_years:.1f} / {required_years:.1f} years)"
                else:
                    # This shouldn't happen (required_years == 0 handled above), but safety check
                    experience_score = 1.0
                    summary = f"Experience: {total_years:.1f} years"
            
            return min(1.0, max(0.0, experience_score)), {
                'resume_years': total_years,
                'required_years': required_years,
                'preferred_years': preferred_years,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error calculating experience match: {str(e)}", exc_info=True)
            return 0.0, {'summary': 'Error calculating experience match'}
    
    def _extract_experience_from_text(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract experience from resume text using date-range patterns (NO section header required)
        Returns format matching experience_parser output
        """
        experiences = []
        total_years = 0.0
        
        if not resume_text or len(resume_text) < 50:
            return {'total_experience_years': 0.0, 'experiences': [], 'summary': ''}
        
        try:
            # Pattern 1: YYYY – Present / YYYY - YYYY
            pattern1 = r'(\d{4})\s*[-–to]+\s*(present|current|now|\d{4})'
            matches1 = re.finditer(pattern1, resume_text, re.IGNORECASE)
            
            # Pattern 2: Month YYYY – Month YYYY / Present
            months = r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*'
            pattern2 = rf'({months}\s+\d{{4}})\s*[-–]\s*(present|current|now|{months}\s+\d{{4}})'
            matches2 = re.finditer(pattern2, resume_text, re.IGNORECASE)
            
            # Pattern 3: MM/YYYY – MM/YYYY
            pattern3 = r'(\d{1,2}[/-]\d{4})\s*[-–]\s*(present|current|now|\d{1,2}[/-]\d{4})'
            matches3 = re.finditer(pattern3, resume_text, re.IGNORECASE)
            
            all_matches = list(matches1) + list(matches2) + list(matches3)
            
            date_ranges = []
            for match in all_matches:
                start_str = match.group(1).strip()
                end_str = match.group(2).strip().lower()
                
                try:
                    from dateparser import parse as parse_date
                    start_date = parse_date(start_str)
                    
                    if start_date:
                        if end_str in ['present', 'current', 'now']:
                            end_date = datetime.now()
                        else:
                            end_date = parse_date(end_str)
                            if not end_date:
                                continue
                        
                        # Calculate duration
                        delta = end_date - start_date
                        years = delta.days / 365.25
                        
                        if years > 0:
                            date_ranges.append({
                                'start': start_date,
                                'end': end_date,
                                'start_str': start_str,
                                'end_str': end_str,
                                'years': years
                            })
                except Exception as e:
                    logger.debug(f"Error parsing date range {start_str} - {end_str}: {e}")
                    continue
            
            # Merge overlapping date ranges
            if date_ranges:
                # Sort by start date
                date_ranges.sort(key=lambda x: x['start'])
                
                merged_ranges = []
                current_range = date_ranges[0]
                
                for next_range in date_ranges[1:]:
                    # Check if ranges overlap or are adjacent (within 3 months)
                    gap = (next_range['start'] - current_range['end']).days
                    if gap <= 90:  # 3 months gap tolerance
                        # Merge ranges
                        current_range['end'] = max(current_range['end'], next_range['end'])
                        current_range['years'] = (current_range['end'] - current_range['start']).days / 365.25
                    else:
                        # No overlap, save current and start new
                        merged_ranges.append(current_range)
                        current_range = next_range
                
                merged_ranges.append(current_range)
                
                # Extract job titles near date ranges (look 200 chars before date)
                for date_range in merged_ranges:
                    start_pos = resume_text.lower().find(date_range['start_str'].lower())
                    if start_pos > 0:
                        # Look for job title before date (up to 200 chars)
                        context_start = max(0, start_pos - 200)
                        context = resume_text[context_start:start_pos]
                        
                        # Common HR job title patterns
                        title_patterns = [
                            r'(?:senior|junior|lead|principal|staff|associate)?\s*(?:hr|human\s+resources|recruitment|talent)\s+(?:manager|director|executive|specialist|coordinator|analyst|generalist)',
                            r'(?:hr|human\s+resources|recruitment|talent)\s+(?:manager|director|executive|specialist|coordinator|analyst|generalist)',
                            r'(?:people|employee|workforce|talent)\s+(?:manager|director|executive)',
                        ]
                        
                        job_title = None
                        for pattern in title_patterns:
                            title_match = re.search(pattern, context, re.IGNORECASE)
                            if title_match:
                                job_title = title_match.group(0).strip()
                                break
                        
                        # If no title found, try to extract from line before date
                        if not job_title:
                            lines = context.split('\n')
                            if len(lines) > 0:
                                potential_title = lines[-1].strip()
                                if len(potential_title) > 5 and len(potential_title) < 100:
                                    job_title = potential_title
                        
                        # Create position dict for internship check
                        position_dict = {
                            'title': job_title or 'Position',
                            'start_date': date_range['start'].isoformat() if isinstance(date_range['start'], datetime) else str(date_range['start']),
                            'end_date': date_range['end'].isoformat() if isinstance(date_range['end'], datetime) else str(date_range['end']),
                            'duration_years': round(date_range['years'], 1),
                            'is_current': date_range['end_str'] in ['present', 'current', 'now']
                        }
                        
                        # CRITICAL: Skip internships (do NOT count toward experience)
                        if self._is_internship_position(position_dict):
                            logger.debug(f"Excluding internship from date-range extraction: {position_dict.get('title')}")
                            continue
                        
                        experiences.append(position_dict)
                        total_years += date_range['years']
            
            # Calculate total
            total_years = round(total_years, 1)
            
            summary = f"{len(experiences)} positions, {total_years} years total"
            if experiences:
                current_pos = next((exp for exp in experiences if exp.get('is_current')), None)
                if current_pos:
                    summary += f", currently {current_pos['title']}"
            
            return {
                'total_experience_years': total_years,
                'experiences': experiences,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error in _extract_experience_from_text: {str(e)}", exc_info=True)
            return {'total_experience_years': 0.0, 'experiences': [], 'summary': ''}
    
    def _extract_experience_from_text_patterns(self, resume_text: str) -> float:
        """
        Extract experience from text patterns like "8+ years of experience"
        Returns total years as float
        """
        if not resume_text:
            return 0.0
        
        resume_text_lower = resume_text.lower()
        max_years = 0.0
        
        # Comprehensive regex patterns for experience text
        patterns = [
            r'(\d+(?:\.\d+)?)\s*\+\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'over\s+(\d+(?:\.\d+)?)\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'more\s+than\s+(\d+(?:\.\d+)?)\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+(?:\.\d+)?)\s*years?\s*of\s*experience',
            r'(\d+(?:\.\d+)?)\s*years?\s*experience',
            r'(\d+(?:\.\d+)?)\s*years?\s*exp',
            r'(\d+(?:\.\d+)?)\s*years?\s*in\s*(?:hr|human\s+resources|recruitment)',
            r'(\d+(?:\.\d+)?)\s*years?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, resume_text_lower)
            if matches:
                try:
                    # Handle tuple matches (for range patterns)
                    if isinstance(matches[0], tuple):
                        # Take the higher number from range
                        nums = [float(m) for m in matches[0] if m and m.replace('.', '').isdigit()]
                        if nums:
                            max_years = max(max_years, max(nums))
                    else:
                        # Single number match
                        nums = [float(m) for m in matches if isinstance(m, str) and m.replace('.', '').isdigit()]
                        if nums:
                            max_years = max(max_years, max(nums))
                    
                    if max_years > 0:
                        logger.debug(f"Text pattern '{pattern}' found {max_years} years")
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error parsing regex match: {e}")
                    continue
        
        return round(max_years, 1)
    
    def _calculate_semantic_similarity(
        self,
        resume: Resume,
        job_embedding: Optional[np.ndarray],
        raw_text: str = ''
    ) -> float:
        """Calculate semantic similarity using embeddings (0-1) - always from raw_text"""
        try:
            if job_embedding is None:
                logger.warning("Job embedding is None, using fallback semantic score")
                return 0.3  # Fallback score instead of 0
            
            # Get raw_text if not provided
            if not raw_text or len(raw_text.strip()) < 10:
                resume_data = resume.parsed_data_json or {}
                raw_text = resume_data.get('raw_text', '') or resume.file_name or ''
            
            # Get resume embedding
            resume_embedding = None
            if resume.embedding_vector:
                try:
                    # Handle both Vector type and JSONB (list)
                    if isinstance(resume.embedding_vector, list):
                        resume_embedding = np.array(resume.embedding_vector, dtype=np.float32)
                    else:
                        resume_embedding = np.array(resume.embedding_vector, dtype=np.float32)
                    
                    # Validate embedding shape
                    if resume_embedding.shape[0] != job_embedding.shape[0]:
                        logger.warning(f"Embedding dimension mismatch: resume={resume_embedding.shape[0]}, job={job_embedding.shape[0]}")
                        resume_embedding = None
                except Exception as e:
                    logger.warning(f"Error converting resume embedding: {str(e)}")
                    resume_embedding = None
            
            # ALWAYS generate embedding from raw_text at match time (don't rely on stored embedding)
            if resume_embedding is None or raw_text:
                if raw_text and len(raw_text.strip()) >= 10:
                    try:
                        logger.debug(f"Generating embedding from raw_text (length={len(raw_text)})")
                        resume_embedding = embedding_generator.generate_bert_embedding(raw_text)
                        if resume_embedding is None:
                            logger.warning("Failed to generate embedding from resume text, using fallback")
                            return self._fallback_semantic_score(raw_text, {})
                    except Exception as e:
                        logger.warning(f"Error generating embedding: {str(e)}")
                        return self._fallback_semantic_score(raw_text, {})
                else:
                    # Very basic fallback
                    logger.warning("raw_text too short, using fallback semantic score")
                    return 0.3  # Give some baseline score instead of 0
            
            if resume_embedding is None:
                return 0.3  # Fallback score
            
            # Calculate cosine similarity
            job_emb = job_embedding / (np.linalg.norm(job_embedding) + 1e-8)
            resume_emb = resume_embedding / (np.linalg.norm(resume_embedding) + 1e-8)
            
            similarity = np.dot(job_emb, resume_emb)
            
            # Normalize to 0-1 range (cosine similarity is -1 to 1, normalize to 0-1)
            # Most similarities are positive, so we use a more generous normalization
            similarity = max(0.0, min(1.0, (similarity + 1) / 2))
            
            # Ensure minimum score for related content (HR resumes for HR jobs should never be 0)
            if similarity < 0.4:
                similarity = 0.4  # Minimum baseline for related content
                logger.debug(f"Applied minimum semantic score (0.4) for related content")
            
            logger.debug(f"Semantic similarity: {similarity:.3f}")
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {str(e)}", exc_info=True)
            return 0.3  # Return fallback score instead of 0
    
    def _fallback_semantic_score(self, resume_text: str, resume_data: Dict[str, Any]) -> float:
        """Fallback semantic score based on keyword matching when embeddings fail"""
        try:
            # Extract keywords from resume
            resume_keywords = set()
            if resume_text:
                # Simple keyword extraction
                words = resume_text.lower().split()
                resume_keywords.update([w for w in words if len(w) > 4])
            
            # Add skills as keywords
            skills_data = resume_data.get('skills', {})
            if isinstance(skills_data, dict):
                skills_list = skills_data.get('extracted', []) or skills_data.get('skills', [])
                resume_keywords.update([s.lower() for s in skills_list if s])
            
            # Basic scoring: if we have keywords, give some score
            if resume_keywords:
                return 0.4  # Moderate fallback score
            else:
                return 0.2  # Low fallback score
        except Exception:
            return 0.3  # Default fallback
    
    def _extract_candidate_name(self, resume_data: Dict[str, Any]) -> str:
        """Extract candidate name from resume data"""
        try:
            contact_info = resume_data.get('contact_info', {})
            if isinstance(contact_info, dict):
                name = contact_info.get('name') or contact_info.get('full_name') or ''
                return name if name else 'Anonymous'
            return 'Anonymous'
        except Exception:
            return 'Anonymous'


# Singleton instance
candidate_matcher = CandidateMatcher()

