"""
Skill Extractor Service
Extracts and normalizes technical skills from resume text using spaCy NER
"""
import logging
import re
from typing import Dict, List, Tuple, Set, Optional, Any
from collections import defaultdict
import spacy
from spacy import displacy

logger = logging.getLogger(__name__)


class SkillExtractor:
    """Extract and normalize technical skills from resume text"""
    
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Skill normalization dictionary (synonyms mapping)
        self.skill_normalization = self._load_skill_normalization()
        
        # Skill categories
        self.skill_categories = {
            'Programming Languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
                'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl'
            ],
            'Web Frameworks': [
                'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring',
                'express', 'next.js', 'nuxt', 'laravel', 'rails', 'asp.net'
            ],
            'Databases': [
                'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
                'oracle', 'sql server', 'dynamodb', 'couchdb', 'neo4j'
            ],
            'Cloud & DevOps': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab ci',
                'terraform', 'ansible', 'chef', 'puppet', 'vagrant', 'prometheus'
            ],
            'Data Science & ML': [
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
                'jupyter', 'matplotlib', 'seaborn', 'plotly', 'spark', 'hadoop'
            ],
            'Tools & Others': [
                'git', 'linux', 'bash', 'powershell', 'jira', 'confluence', 'slack',
                'postman', 'swagger', 'graphql', 'rest api', 'microservices'
            ]
        }
        
        # Build reverse lookup for categories
        self.skill_to_category = {}
        for category, skills in self.skill_categories.items():
            for skill in skills:
                self.skill_to_category[skill.lower()] = category
    
    def _load_skill_normalization(self) -> Dict[str, str]:
        """Load skill normalization dictionary"""
        return {
            # Programming Languages
            'js': 'javascript',
            'ts': 'typescript',
            'cplusplus': 'c++',
            'cpp': 'c++',
            'csharp': 'c#',
            'golang': 'go',
            'node': 'node.js',
            'nodejs': 'node.js',
            
            # Frameworks
            'reactjs': 'react',
            'react.js': 'react',
            'vuejs': 'vue',
            'vue.js': 'vue',
            'angularjs': 'angular',
            'angular.js': 'angular',
            
            # Databases
            'postgres': 'postgresql',
            'pg': 'postgresql',
            'mongo': 'mongodb',
            'ms sql': 'sql server',
            'mssql': 'sql server',
            
            # Cloud
            'amazon web services': 'aws',
            'google cloud': 'gcp',
            'google cloud platform': 'gcp',
            
            # DevOps
            'k8s': 'kubernetes',
            'kube': 'kubernetes',
            'ci/cd': 'continuous integration',
            'cicd': 'continuous integration',
        }
    
    def extract_skills(self, text: str, min_confidence: float = 0.5) -> Dict[str, Any]:
        """
        Extract skills from resume text
        
        Args:
            text: Resume text
            min_confidence: Minimum confidence score for skill extraction
            
        Returns:
            Dictionary with extracted skills, categories, and confidence scores
        """
        if not self.nlp:
            logger.warning("spaCy model not loaded, using basic extraction")
            return self._basic_skill_extraction(text)
        
        try:
            doc = self.nlp(text.lower())
            
            # Extract skills using multiple methods
            skills_set = set()
            skill_mentions = defaultdict(int)
            
            # Method 1: Named Entity Recognition
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'TECH']:
                    skill = self._normalize_skill(ent.text)
                    if skill:
                        skills_set.add(skill)
                        skill_mentions[skill] += 1
            
            # Method 2: Pattern matching with known skills
            all_known_skills = set()
            for category_skills in self.skill_categories.values():
                all_known_skills.update(category_skills)
            
            text_lower = text.lower()
            for skill in all_known_skills:
                # Use word boundaries for exact matching
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    normalized = self._normalize_skill(skill)
                    if normalized:
                        skills_set.add(normalized)
                        skill_mentions[normalized] += len(re.findall(pattern, text_lower))
            
            # Method 3: Extract from "Skills" section
            skills_section = self._extract_skills_section(text)
            for skill in skills_section:
                normalized = self._normalize_skill(skill)
                if normalized:
                    skills_set.add(normalized)
                    skill_mentions[normalized] += 1
            
            # Categorize skills
            categorized_skills = self._categorize_skills(list(skills_set))
            
            # Calculate confidence scores
            skill_scores = self._calculate_confidence_scores(
                list(skills_set),
                skill_mentions,
                text
            )
            
            # Filter by confidence
            filtered_skills = {
                skill: score for skill, score in skill_scores.items()
                if score >= min_confidence
            }
            
            return {
                'skills': list(filtered_skills.keys()),
                'skill_scores': filtered_skills,
                'categorized_skills': categorized_skills,
                'total_skills': len(filtered_skills),
                'skill_mentions': dict(skill_mentions)
            }
            
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}", exc_info=True)
            return self._basic_skill_extraction(text)
    
    def _normalize_skill(self, skill: str) -> Optional[str]:
        """Normalize skill name using normalization dictionary"""
        skill_lower = skill.lower().strip()
        
        # Check normalization dictionary
        if skill_lower in self.skill_normalization:
            return self.skill_normalization[skill_lower]
        
        # Return original if already normalized
        return skill_lower if skill_lower else None
    
    def _extract_skills_section(self, text: str) -> List[str]:
        """Extract skills from dedicated skills section"""
        skills = []
        
        # Find skills section
        skills_pattern = re.compile(
            r'(?:skills?|technical\s+skills?|competencies?|expertise)[:;]?\s*\n(.*?)(?:\n\n|\n[A-Z]|$)',
            re.IGNORECASE | re.DOTALL
        )
        
        match = skills_pattern.search(text)
        if match:
            skills_text = match.group(1)
            # Split by common delimiters
            skills = re.split(r'[,;•\-\n]', skills_text)
            skills = [s.strip() for s in skills if s.strip()]
        
        return skills
    
    def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills into predefined categories"""
        categorized = defaultdict(list)
        
        for skill in skills:
            category = self.skill_to_category.get(skill.lower(), 'Other')
            categorized[category].append(skill)
        
        return dict(categorized)
    
    def _calculate_confidence_scores(
        self,
        skills: List[str],
        mentions: Dict[str, int],
        text: str
    ) -> Dict[str, float]:
        """Calculate confidence scores for extracted skills"""
        scores = {}
        text_lower = text.lower()
        
        for skill in skills:
            score = 0.0
            
            # Base score from mentions
            mention_count = mentions.get(skill, 0)
            if mention_count > 0:
                score += min(mention_count * 0.2, 0.6)  # Max 0.6 from mentions
            
            # Bonus for being in skills section
            if self._is_in_skills_section(skill, text):
                score += 0.3
            
            # Bonus for being a known skill
            if skill.lower() in self.skill_to_category:
                score += 0.1
            
            scores[skill] = min(score, 1.0)
        
        return scores
    
    def _is_in_skills_section(self, skill: str, text: str) -> bool:
        """Check if skill appears in dedicated skills section"""
        skills_section = self._extract_skills_section(text)
        return skill.lower() in [s.lower() for s in skills_section]
    
    def _basic_skill_extraction(self, text: str) -> Dict[str, Any]:
        """Basic skill extraction without spaCy (fallback)"""
        text_lower = text.lower()
        skills_set = set()
        
        # Extract known skills
        all_known_skills = set()
        for category_skills in self.skill_categories.values():
            all_known_skills.update(category_skills)
        
        for skill in all_known_skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                normalized = self._normalize_skill(skill)
                if normalized:
                    skills_set.add(normalized)
        
        categorized = self._categorize_skills(list(skills_set))
        
        return {
            'skills': list(skills_set),
            'skill_scores': {skill: 0.7 for skill in skills_set},
            'categorized_skills': categorized,
            'total_skills': len(skills_set),
            'skill_mentions': {}
        }


# Singleton instance
skill_extractor = SkillExtractor()

