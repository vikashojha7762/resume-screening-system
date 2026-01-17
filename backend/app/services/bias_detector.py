"""
Bias Detection & Mitigation System
Detects and mitigates various forms of bias in hiring
"""
import logging
import re
from typing import Dict, List, Optional, Any, Set
from collections import Counter

logger = logging.getLogger(__name__)


class BiasDetector:
    """Detect and mitigate bias in job descriptions and candidate evaluation"""
    
    def __init__(self):
        # Gender-biased words
        self.gender_biased_words = {
            'masculine': [
                'aggressive', 'ambitious', 'assertive', 'competitive', 'confident',
                'decisive', 'determined', 'dominant', 'independent', 'leader',
                'logical', 'objective', 'outspoken', 'strong', 'tough'
            ],
            'feminine': [
                'collaborative', 'compassionate', 'cooperative', 'emotional',
                'gentle', 'helpful', 'nurturing', 'sensitive', 'supportive',
                'understanding', 'warm', 'caring', 'empathetic'
            ]
        }
        
        # Age-related patterns
        self.age_patterns = [
            r'\b\d{2,3}\s*years?\s+old\b',
            r'\b(recent|new)\s+graduate\b',
            r'\b(fresh|young)\s+talent\b',
            r'\bseasoned\s+professional\b',
            r'\bexperienced\s+executive\b'
        ]
        
        # Institution bias keywords
        self.institution_bias_keywords = [
            'ivy league', 'top tier', 'prestigious', 'elite',
            'top university', 'leading institution'
        ]
    
    def detect_job_description_bias(
        self,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Detect various forms of bias in job description
        
        Returns:
            Dictionary with bias detection results
        """
        results = {
            'gender_bias': self._detect_gender_bias(job_description),
            'age_bias': self._detect_age_bias(job_description),
            'institution_bias': self._detect_institution_bias(job_description),
            'overall_bias_score': 0.0,
            'recommendations': []
        }
        
        # Calculate overall bias score
        bias_scores = [
            results['gender_bias']['score'],
            results['age_bias']['score'],
            results['institution_bias']['score']
        ]
        results['overall_bias_score'] = max(bias_scores)
        
        # Generate recommendations
        results['recommendations'] = self._generate_bias_recommendations(results)
        
        return results
    
    def _detect_gender_bias(self, text: str) -> Dict[str, Any]:
        """Detect gender-biased language"""
        text_lower = text.lower()
        
        masculine_count = sum(
            1 for word in self.gender_biased_words['masculine']
            if word in text_lower
        )
        feminine_count = sum(
            1 for word in self.gender_biased_words['feminine']
            if word in text_lower
        )
        
        total_biased = masculine_count + feminine_count
        bias_ratio = abs(masculine_count - feminine_count) / max(total_biased, 1)
        
        # Score: 0 (no bias) to 1 (high bias)
        score = min(bias_ratio * 0.5 + (total_biased / 20.0) * 0.5, 1.0)
        
        return {
            'detected': total_biased > 0,
            'score': score,
            'masculine_words_found': masculine_count,
            'feminine_words_found': feminine_count,
            'biased_words': self._find_biased_words(text_lower)
        }
    
    def _detect_age_bias(self, text: str) -> Dict[str, Any]:
        """Detect age-related bias"""
        text_lower = text.lower()
        matches = []
        
        for pattern in self.age_patterns:
            found = re.findall(pattern, text_lower, re.IGNORECASE)
            matches.extend(found)
        
        score = min(len(matches) / 5.0, 1.0)  # Max score at 5+ matches
        
        return {
            'detected': len(matches) > 0,
            'score': score,
            'matches_found': len(matches),
            'patterns': matches
        }
    
    def _detect_institution_bias(self, text: str) -> Dict[str, Any]:
        """Detect institution bias"""
        text_lower = text.lower()
        matches = []
        
        for keyword in self.institution_bias_keywords:
            if keyword in text_lower:
                matches.append(keyword)
        
        score = min(len(matches) / 3.0, 1.0)  # Max score at 3+ matches
        
        return {
            'detected': len(matches) > 0,
            'score': score,
            'matches_found': len(matches),
            'keywords': matches
        }
    
    def _find_biased_words(self, text: str) -> List[str]:
        """Find all biased words in text"""
        found = []
        all_biased = (
            self.gender_biased_words['masculine'] +
            self.gender_biased_words['feminine']
        )
        
        for word in all_biased:
            if word in text:
                found.append(word)
        
        return found
    
    def _generate_bias_recommendations(
        self,
        bias_results: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations to reduce bias"""
        recommendations = []
        
        if bias_results['gender_bias']['score'] > 0.3:
            recommendations.append(
                "Consider using more gender-neutral language. "
                "Balance masculine and feminine descriptors."
            )
        
        if bias_results['age_bias']['score'] > 0.3:
            recommendations.append(
                "Remove age-related language. Focus on skills and experience "
                "rather than age or years since graduation."
            )
        
        if bias_results['institution_bias']['score'] > 0.3:
            recommendations.append(
                "Avoid specifying institution tiers. Focus on skills and "
                "competencies rather than where candidates studied."
            )
        
        if not recommendations:
            recommendations.append("Job description appears relatively unbiased.")
        
        return recommendations
    
    def anonymize_resume(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize resume data for blind screening
        
        Removes PII and identifying information
        """
        anonymized = resume_data.copy()
        
        # Remove contact information
        if 'contact_info' in anonymized:
            anonymized['contact_info'] = {
                'email': '***@***.***',
                'phone': '***-***-****',
                'linkedin': None,
                'github': None,
                'website': None
            }
        
        # Anonymize names in text
        if 'raw_text' in anonymized:
            anonymized['raw_text'] = self._anonymize_text(anonymized['raw_text'])
        
        # Remove identifying information from experience
        if 'experience' in anonymized and 'experiences' in anonymized['experience']:
            for exp in anonymized['experience']['experiences']:
                # Keep company but anonymize specific details
                if 'achievements' in exp:
                    exp['achievements'] = [
                        self._anonymize_text(ach) for ach in exp.get('achievements', [])
                    ]
        
        # Anonymize education institutions (keep degree and field)
        if 'education' in anonymized and 'educations' in anonymized['education']:
            for edu in anonymized['education']['educations']:
                if 'institution' in edu:
                    edu['institution'] = '*** University'
        
        return anonymized
    
    def _anonymize_text(self, text: str) -> str:
        """Anonymize names and PII in text"""
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***@***.***', text)
        
        # Remove phone numbers
        text = re.sub(r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}', '***-***-****', text)
        
        # Remove URLs
        text = re.sub(r'https?://[^\s]+', '***', text)
        
        # Simple name detection (capitalized words that might be names)
        # This is basic - can be enhanced with NER
        words = text.split()
        anonymized_words = []
        for word in words:
            if word[0].isupper() and len(word) > 2 and word.isalpha():
                # Might be a name, replace with generic
                anonymized_words.append('***')
            else:
                anonymized_words.append(word)
        
        return ' '.join(anonymized_words)
    
    def mask_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask personally identifiable information"""
        masked = data.copy()
        
        # Mask email
        if 'email' in masked:
            masked['email'] = '***@***.***'
        
        # Mask phone
        if 'phone' in masked:
            masked['phone'] = '***-***-****'
        
        # Mask names (if present)
        if 'name' in masked:
            masked['name'] = '***'
        
        return masked


# Singleton instance
bias_detector = BiasDetector()

