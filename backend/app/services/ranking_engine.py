"""
Candidate Ranking System
Sorts and ranks candidates with tie-breaking and explanations
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class RankingEngine:
    """Rank candidates based on match scores"""
    
    def __init__(self):
        # Tie-breaking priority order
        self.tie_break_priority = [
            'overall_score',
            'experience_years',
            'education_level',
            'recency_score'
        ]
    
    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        job_id: str,
        diversity_weight: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Rank candidates by score with tie-breaking and diversity
        
        Args:
            candidates: List of candidate data with scores
            job_id: Job ID for context
            diversity_weight: Weight for diversity scoring (0-1)
            
        Returns:
            Ranked list of candidates with explanations
        """
        try:
            logger.info(f"Ranking {len(candidates)} candidates for job {job_id}")
            
            # Calculate diversity scores if enabled
            if diversity_weight > 0:
                diversity_scores = self._calculate_diversity_scores(candidates)
                for i, candidate in enumerate(candidates):
                    candidate['diversity_score'] = diversity_scores.get(i, 0.0)
                    # Adjust overall score with diversity
                    candidate['overall_score'] = (
                        candidate['overall_score'] * (1 - diversity_weight) +
                        candidate['diversity_score'] * diversity_weight
                    )
            
            # Sort candidates
            ranked = self._sort_candidates(candidates)
            
            # Assign ranks
            for idx, candidate in enumerate(ranked, start=1):
                candidate['rank'] = idx
                candidate['ranking_explanation'] = self._generate_ranking_explanation(
                    candidate, idx, len(ranked)
                )
            
            # Cluster similar candidates
            clusters = self._cluster_similar_candidates(ranked)
            
            return {
                'ranked_candidates': ranked,
                'total_candidates': len(ranked),
                'clusters': clusters,
                'diversity_enabled': diversity_weight > 0
            }
            
        except Exception as e:
            logger.error(f"Error ranking candidates: {str(e)}", exc_info=True)
            return {
                'ranked_candidates': candidates,
                'total_candidates': len(candidates),
                'error': str(e)
            }
    
    def _sort_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort candidates using tie-breaking rules"""
        def sort_key(candidate: Dict[str, Any]) -> Tuple:
            """Multi-level sort key"""
            # Primary: overall score (descending)
            overall = candidate.get('overall_score', 0.0)
            
            # Secondary: experience years (descending)
            exp_data = candidate.get('resume_data', {}).get('experience', {})
            exp_years = exp_data.get('total_experience_years', 0.0)
            
            # Tertiary: education level (descending)
            edu_data = candidate.get('resume_data', {}).get('education', {})
            highest_degree = edu_data.get('highest_degree', '')
            edu_level = self._get_education_level(highest_degree)
            
            # Quaternary: recency (most recent first)
            recency = self._calculate_recency_score(candidate)
            
            return (-overall, -exp_years, -edu_level, -recency)
        
        return sorted(candidates, key=sort_key, reverse=False)
    
    def _get_education_level(self, degree: str) -> int:
        """Get education level as integer for sorting"""
        degree_lower = degree.lower()
        if 'phd' in degree_lower or 'doctorate' in degree_lower:
            return 5
        elif 'master' in degree_lower or 'mba' in degree_lower:
            return 4
        elif 'bachelor' in degree_lower or 'bs' in degree_lower or 'ba' in degree_lower:
            return 3
        elif 'associate' in degree_lower:
            return 2
        elif 'diploma' in degree_lower or 'certificate' in degree_lower:
            return 1
        return 0
    
    def _calculate_recency_score(self, candidate: Dict[str, Any]) -> float:
        """Calculate recency score based on most recent experience"""
        experiences = candidate.get('resume_data', {}).get('experience', {}).get('experiences', [])
        
        if not experiences:
            return 0.0
        
        # Find most recent end date
        most_recent = None
        for exp in experiences:
            if exp.get('is_current'):
                return 1.0  # Currently employed
            end_date = exp.get('end_date')
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if most_recent is None or end_dt > most_recent:
                        most_recent = end_dt
                except:
                    pass
        
        if most_recent:
            # Calculate years since last employment
            years_ago = (datetime.now() - most_recent.replace(tzinfo=None)).days / 365.25
            # Score decreases with time (max 1.0 for recent, 0.0 for >5 years)
            return max(0.0, 1.0 - (years_ago / 5.0))
        
        return 0.5  # Default if no dates
    
    def _calculate_diversity_scores(
        self,
        candidates: List[Dict[str, Any]]
    ) -> Dict[int, float]:
        """Calculate diversity scores for balanced hiring"""
        diversity_scores = {}
        
        # Extract diversity attributes (anonymized)
        attributes = []
        for candidate in candidates:
            attr = {
                'institution_tier': self._get_institution_tier(candidate),
                'experience_level': self._get_experience_level(candidate),
                'skill_diversity': self._get_skill_diversity(candidate)
            }
            attributes.append(attr)
        
        # Calculate diversity for each candidate
        for i, candidate in enumerate(candidates):
            score = 0.0
            
            # Institution diversity (reward candidates from underrepresented institutions)
            institution_counts = defaultdict(int)
            for attr in attributes:
                institution_counts[attr['institution_tier']] += 1
            
            candidate_tier = attributes[i]['institution_tier']
            tier_count = institution_counts[candidate_tier]
            if tier_count < len(candidates) / 3:  # Less than 1/3 from this tier
                score += 0.3
            
            # Experience diversity
            exp_levels = [a['experience_level'] for a in attributes]
            candidate_level = attributes[i]['experience_level']
            if exp_levels.count(candidate_level) < len(candidates) / 2:
                score += 0.3
            
            # Skill diversity (reward unique skill combinations)
            skill_diversity = attributes[i]['skill_diversity']
            similar_count = sum(
                1 for a in attributes
                if abs(a['skill_diversity'] - skill_diversity) < 0.1
            )
            if similar_count < len(candidates) / 2:
                score += 0.4
            
            diversity_scores[i] = min(score, 1.0)
        
        return diversity_scores
    
    def _get_institution_tier(self, candidate: Dict[str, Any]) -> str:
        """Get institution tier for diversity calculation"""
        educations = candidate.get('resume_data', {}).get('education', {}).get('educations', [])
        if educations:
            institution = educations[0].get('institution', '').lower()
            # Simple tier detection (can be enhanced)
            tier1_keywords = ['mit', 'stanford', 'harvard', 'caltech', 'princeton']
            tier2_keywords = ['university', 'college']
            if any(kw in institution for kw in tier1_keywords):
                return 'tier1'
            elif any(kw in institution for kw in tier2_keywords):
                return 'tier2'
        return 'tier3'
    
    def _get_experience_level(self, candidate: Dict[str, Any]) -> str:
        """Get experience level category"""
        exp_years = candidate.get('resume_data', {}).get('experience', {}).get('total_experience_years', 0)
        if exp_years >= 7:
            return 'senior'
        elif exp_years >= 3:
            return 'mid'
        else:
            return 'junior'
    
    def _get_skill_diversity(self, candidate: Dict[str, Any]) -> float:
        """Calculate skill diversity score"""
        skills = candidate.get('resume_data', {}).get('skills', {}).get('categorized_skills', {})
        # Count unique categories
        return len(skills) / 6.0  # Normalize by max categories
    
    def _cluster_similar_candidates(
        self,
        ranked_candidates: List[Dict[str, Any]],
        similarity_threshold: float = 0.85
    ) -> Dict[str, List[int]]:
        """Cluster candidates with similar scores"""
        clusters = defaultdict(list)
        current_cluster = 0
        
        for i, candidate in enumerate(ranked_candidates):
            score = candidate.get('overall_score', 0.0)
            
            # Find existing cluster with similar score
            assigned = False
            for cluster_id, members in clusters.items():
                if members:
                    cluster_avg = np.mean([
                        ranked_candidates[m].get('overall_score', 0.0)
                        for m in members
                    ])
                    if abs(score - cluster_avg) < (1 - similarity_threshold):
                        clusters[cluster_id].append(i)
                        assigned = True
                        break
            
            if not assigned:
                # Create new cluster
                clusters[f'cluster_{current_cluster}'].append(i)
                current_cluster += 1
        
        return dict(clusters)
    
    def _generate_ranking_explanation(
        self,
        candidate: Dict[str, Any],
        rank: int,
        total: int
    ) -> str:
        """Generate explanation for candidate's ranking"""
        explanations = []
        
        # Rank position
        if rank == 1:
            explanations.append("Top candidate")
        elif rank <= 3:
            explanations.append(f"Top {rank} candidate")
        elif rank <= total * 0.1:
            explanations.append("Top 10% candidate")
        elif rank <= total * 0.25:
            explanations.append("Top 25% candidate")
        else:
            explanations.append(f"Ranked {rank} of {total}")
        
        # Score-based explanation
        score = candidate.get('overall_score', 0.0)
        if score >= 0.8:
            explanations.append("with excellent match score")
        elif score >= 0.6:
            explanations.append("with good match score")
        else:
            explanations.append("with moderate match score")
        
        # Component strengths
        component_scores = candidate.get('component_scores', {})
        if component_scores.get('skills', 0) >= 0.8:
            explanations.append("Strong skills match")
        if component_scores.get('experience', 0) >= 0.8:
            explanations.append("Strong experience match")
        
        return ". ".join(explanations) + "."


# Singleton instance
ranking_engine = RankingEngine()

