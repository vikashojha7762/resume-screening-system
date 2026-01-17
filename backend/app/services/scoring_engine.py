"""
Scoring Engine for Resume-Job Matching
Implements rule-based and weighted scoring algorithms
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
import re

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Calculate match scores between resumes and job requirements"""
    
    def __init__(self):
        # Default weights (can be configured)
        self.default_weights = {
            'skills': 0.50,
            'experience': 0.30,
            'education': 0.20
        }
        
        # Skill match thresholds
        self.skill_match_scores = {
            'exact': 1.0,
            'partial': 0.7,
            'related': 0.3
        }
        
        # Experience scoring parameters
        self.experience_params = {
            'min_years': 0,
            'max_years': 10,  # Diminishing returns after 10 years
            'diminishing_factor': 0.8
        }
    
    def calculate_match_score(
        self,
        resume_data: Dict[str, Any],
        job_requirements: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive match score between resume and job
        
        Args:
            resume_data: Parsed resume data
            job_requirements: Job requirements and preferences
            weights: Custom weights (defaults to self.default_weights)
            
        Returns:
            Dictionary with scores, breakdown, and explanations
        """
        weights = weights or self.default_weights
        
        try:
            # Validate weights sum to 1.0
            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) > 0.01:
                logger.warning(f"Weights sum to {total_weight}, normalizing")
                weights = {k: v / total_weight for k, v in weights.items()}
            
            # Calculate component scores
            mandatory_score = self._check_mandatory_requirements(
                resume_data, job_requirements
            )
            
            if mandatory_score == 0:
                # Candidate doesn't meet mandatory requirements
                return {
                    'overall_score': 0.0,
                    'mandatory_met': False,
                    'component_scores': {},
                    'breakdown': {},
                    'explanation': 'Candidate does not meet mandatory requirements'
                }
            
            skill_score, skill_breakdown = self._calculate_skill_score(
                resume_data, job_requirements
            )
            
            experience_score, exp_breakdown = self._calculate_experience_score(
                resume_data, job_requirements
            )
            
            education_score, edu_breakdown = self._calculate_education_score(
                resume_data, job_requirements
            )
            
            # Calculate weighted overall score
            overall_score = (
                skill_score * weights['skills'] +
                experience_score * weights['experience'] +
                education_score * weights['education']
            )
            
            # Generate explanation
            explanation = self._generate_explanation(
                overall_score,
                skill_score,
                experience_score,
                education_score,
                skill_breakdown,
                exp_breakdown,
                edu_breakdown
            )
            
            return {
                'overall_score': round(overall_score, 2),
                'mandatory_met': True,
                'component_scores': {
                    'skills': round(skill_score, 2),
                    'experience': round(experience_score, 2),
                    'education': round(education_score, 2)
                },
                'breakdown': {
                    'skills': skill_breakdown,
                    'experience': exp_breakdown,
                    'education': edu_breakdown
                },
                'weights_used': weights,
                'explanation': explanation
            }
            
        except Exception as e:
            logger.error(f"Error calculating match score: {str(e)}", exc_info=True)
            return {
                'overall_score': 0.0,
                'error': str(e)
            }
    
    def _check_mandatory_requirements(
        self,
        resume_data: Dict[str, Any],
        job_requirements: Dict[str, Any]
    ) -> float:
        """Check if candidate meets mandatory requirements"""
        mandatory = job_requirements.get('mandatory_requirements', {})
        
        if not mandatory:
            return 1.0  # No mandatory requirements
        
        # Check mandatory skills
        required_skills = mandatory.get('skills', [])
        if required_skills:
            resume_skills = [
                s.lower() for s in resume_data.get('skills', {}).get('skills', [])
            ]
            for req_skill in required_skills:
                if req_skill.lower() not in resume_skills:
                    logger.info(f"Missing mandatory skill: {req_skill}")
                    return 0.0
        
        # Check minimum experience
        min_experience = mandatory.get('min_experience_years', 0)
        if min_experience > 0:
            total_exp = resume_data.get('experience', {}).get('total_experience_years', 0)
            if total_exp < min_experience:
                logger.info(f"Insufficient experience: {total_exp} < {min_experience}")
                return 0.0
        
        # Check education requirements
        required_degree = mandatory.get('required_degree', None)
        if required_degree:
            highest_degree = resume_data.get('education', {}).get('highest_degree', '')
            degree_hierarchy = {
                'phd': 5,
                'masters': 4,
                'bachelors': 3,
                'associates': 2,
                'diploma': 1
            }
            req_level = degree_hierarchy.get(required_degree.lower(), 0)
            highest_level = 0
            for degree_type, level in degree_hierarchy.items():
                if degree_type in highest_degree.lower():
                    highest_level = level
                    break
            if highest_level < req_level:
                logger.info(f"Insufficient education: {highest_degree}")
                return 0.0
        
        return 1.0
    
    def _calculate_skill_score(
        self,
        resume_data: Dict[str, Any],
        job_requirements: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate skill match score"""
        resume_skills = [
            s.lower() for s in resume_data.get('skills', {}).get('skills', [])
        ]
        required_skills = [
            s.lower() for s in job_requirements.get('required_skills', [])
        ]
        preferred_skills = [
            s.lower() for s in job_requirements.get('preferred_skills', [])
        ]
        
        if not required_skills and not preferred_skills:
            return 1.0, {'matched_skills': [], 'missing_skills': []}
        
        # Calculate matches
        exact_matches = []
        partial_matches = []
        related_matches = []
        missing_required = []
        missing_preferred = []
        
        # Check required skills
        for req_skill in required_skills:
            matched = False
            for res_skill in resume_skills:
                match_type = self._match_skill_type(req_skill, res_skill)
                if match_type == 'exact':
                    exact_matches.append(req_skill)
                    matched = True
                    break
                elif match_type == 'partial':
                    partial_matches.append(req_skill)
                    matched = True
                    break
                elif match_type == 'related':
                    related_matches.append(req_skill)
                    matched = True
                    break
            
            if not matched:
                missing_required.append(req_skill)
        
        # Check preferred skills
        for pref_skill in preferred_skills:
            if pref_skill not in required_skills:
                matched = False
                for res_skill in resume_skills:
                    match_type = self._match_skill_type(pref_skill, res_skill)
                    if match_type in ['exact', 'partial', 'related']:
                        matched = True
                        break
                
                if not matched:
                    missing_preferred.append(pref_skill)
        
        # Calculate score
        total_required = len(required_skills)
        total_preferred = len(preferred_skills)
        
        if total_required == 0 and total_preferred == 0:
            score = 1.0
        else:
            # Required skills are more important
            required_score = 0.0
            if total_required > 0:
                required_score = (
                    len(exact_matches) * self.skill_match_scores['exact'] +
                    len(partial_matches) * self.skill_match_scores['partial'] +
                    len(related_matches) * self.skill_match_scores['related']
                ) / total_required
            
            # Preferred skills contribute less
            preferred_score = 0.0
            if total_preferred > 0:
                matched_preferred = total_preferred - len(missing_preferred)
                preferred_score = matched_preferred / total_preferred * 0.5  # Max 0.5 for preferred
            
            # Weighted combination (70% required, 30% preferred)
            if total_required > 0:
                score = required_score * 0.7 + preferred_score * 0.3
            else:
                score = preferred_score
        
        breakdown = {
            'exact_matches': exact_matches,
            'partial_matches': partial_matches,
            'related_matches': related_matches,
            'missing_required': missing_required,
            'missing_preferred': missing_preferred,
            'match_rate': len(exact_matches + partial_matches + related_matches) / max(total_required + total_preferred, 1)
        }
        
        return min(score, 1.0), breakdown
    
    def _match_skill_type(self, required: str, resume: str) -> str:
        """Determine skill match type"""
        required_lower = required.lower().strip()
        resume_lower = resume.lower().strip()
        
        # Exact match
        if required_lower == resume_lower:
            return 'exact'
        
        # Partial match (one contains the other)
        if required_lower in resume_lower or resume_lower in required_lower:
            return 'partial'
        
        # Related match (common words, synonyms)
        required_words = set(required_lower.split())
        resume_words = set(resume_lower.split())
        common_words = required_words & resume_words
        
        if len(common_words) > 0:
            return 'related'
        
        return 'none'
    
    def _calculate_experience_score(
        self,
        resume_data: Dict[str, Any],
        job_requirements: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate experience match score with diminishing returns"""
        required_years = job_requirements.get('required_experience_years', 0)
        preferred_years = job_requirements.get('preferred_experience_years', required_years)
        
        resume_exp = resume_data.get('experience', {}).get('total_experience_years', 0)
        
        if required_years == 0:
            # No experience requirement
            return 1.0, {'years': resume_exp, 'required': 0}
        
        # Calculate score with diminishing returns
        if resume_exp >= preferred_years:
            # Candidate exceeds preferred experience
            excess = resume_exp - preferred_years
            # Diminishing returns for excess experience
            score = 1.0 - (excess * 0.05)  # 5% penalty per excess year
            score = max(score, 0.7)  # Minimum 70% for over-qualified
        elif resume_exp >= required_years:
            # Candidate meets requirement
            score = 0.7 + ((resume_exp - required_years) / (preferred_years - required_years)) * 0.3
        else:
            # Candidate below requirement
            score = max(0.0, resume_exp / required_years * 0.7)
        
        breakdown = {
            'years': resume_exp,
            'required': required_years,
            'preferred': preferred_years,
            'meets_requirement': resume_exp >= required_years,
            'exceeds_preferred': resume_exp >= preferred_years
        }
        
        return min(score, 1.0), breakdown
    
    def _calculate_education_score(
        self,
        resume_data: Dict[str, Any],
        job_requirements: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate education match score with institution tier consideration"""
        required_degree = job_requirements.get('required_degree', None)
        preferred_institutions = job_requirements.get('preferred_institutions', [])
        institution_tiers = job_requirements.get('institution_tiers', {})
        
        educations = resume_data.get('education', {}).get('educations', [])
        
        if not educations:
            return 0.0, {'has_education': False}
        
        # Check degree requirement
        degree_score = 1.0
        if required_degree:
            highest_degree = resume_data.get('education', {}).get('highest_degree', '')
            degree_hierarchy = {
                'phd': 5,
                'masters': 4,
                'bachelors': 3,
                'associates': 2,
                'diploma': 1
            }
            req_level = degree_hierarchy.get(required_degree.lower(), 0)
            highest_level = 0
            for degree_type, level in degree_hierarchy.items():
                if degree_type in highest_degree.lower():
                    highest_level = level
                    break
            
            if highest_level < req_level:
                degree_score = 0.0
            elif highest_level > req_level:
                degree_score = 1.0  # Over-qualified is fine
            else:
                degree_score = 1.0
        
        # Check institution tier
        institution_score = 1.0
        if preferred_institutions or institution_tiers:
            best_institution = None
            best_tier = None
            
            for edu in educations:
                institution = edu.get('institution', '').lower()
                
                # Check if in preferred list
                if any(pref.lower() in institution for pref in preferred_institutions):
                    best_institution = institution
                    best_tier = 'preferred'
                    break
                
                # Check tier
                for tier, institutions in institution_tiers.items():
                    if any(inst.lower() in institution for inst in institutions):
                        if best_tier is None or self._tier_rank(tier) > self._tier_rank(best_tier):
                            best_institution = institution
                            best_tier = tier
            
            if best_tier:
                tier_scores = {
                    'tier1': 1.0,
                    'tier2': 0.8,
                    'tier3': 0.6,
                    'preferred': 1.0
                }
                institution_score = tier_scores.get(best_tier, 0.5)
            else:
                institution_score = 0.5  # Default for unknown institutions
        
        # Combined score (70% degree, 30% institution)
        final_score = degree_score * 0.7 + institution_score * 0.3
        
        breakdown = {
            'highest_degree': resume_data.get('education', {}).get('highest_degree'),
            'institutions': [e.get('institution') for e in educations],
            'degree_score': degree_score,
            'institution_score': institution_score
        }
        
        return final_score, breakdown
    
    def _tier_rank(self, tier: str) -> int:
        """Get tier ranking (higher is better)"""
        ranks = {'tier1': 3, 'tier2': 2, 'tier3': 1, 'preferred': 4}
        return ranks.get(tier.lower(), 0)
    
    def _generate_explanation(
        self,
        overall_score: float,
        skill_score: float,
        experience_score: float,
        education_score: float,
        skill_breakdown: Dict[str, Any],
        exp_breakdown: Dict[str, Any],
        edu_breakdown: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation of the score"""
        explanations = []
        
        # Overall assessment
        if overall_score >= 0.8:
            explanations.append("Excellent match with strong alignment across all criteria.")
        elif overall_score >= 0.6:
            explanations.append("Good match with solid qualifications.")
        elif overall_score >= 0.4:
            explanations.append("Moderate match with some gaps in requirements.")
        else:
            explanations.append("Limited match with significant gaps.")
        
        # Skills explanation
        if skill_breakdown.get('exact_matches'):
            explanations.append(
                f"Strong skill match with {len(skill_breakdown['exact_matches'])} exact matches."
            )
        if skill_breakdown.get('missing_required'):
            explanations.append(
                f"Missing {len(skill_breakdown['missing_required'])} required skills."
            )
        
        # Experience explanation
        if exp_breakdown.get('meets_requirement'):
            explanations.append(
                f"Meets experience requirement ({exp_breakdown['years']} years)."
            )
        else:
            explanations.append(
                f"Below experience requirement ({exp_breakdown['years']} vs {exp_breakdown['required']} years)."
            )
        
        # Education explanation
        if edu_breakdown.get('highest_degree'):
            explanations.append(
                f"Education: {edu_breakdown['highest_degree']}."
            )
        
        return " ".join(explanations)


# Singleton instance
scoring_engine = ScoringEngine()

