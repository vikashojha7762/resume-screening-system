"""
Experience Parser Service
Extracts work experience, job titles, companies, dates, and achievements
"""
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import dateparser
from collections import defaultdict

logger = logging.getLogger(__name__)


class ExperienceParser:
    """Parse work experience from resume text"""
    
    def __init__(self):
        # Common job title patterns
        self.job_title_patterns = [
            r'(?:Senior|Junior|Lead|Principal|Staff|Associate)?\s*'
            r'(?:Software|Backend|Frontend|Full.?Stack|DevOps|Data|ML|AI)?\s*'
            r'(?:Engineer|Developer|Architect|Scientist|Analyst|Manager|Director)',
            r'(?:Product|Project|Engineering|Technical)?\s*Manager',
            r'(?:Chief|VP|Vice President|Head of)\s+\w+',
        ]
        
        # Company name patterns (handle abbreviations)
        self.company_patterns = [
            r'[A-Z][a-zA-Z0-9\s&]+(?:Inc\.?|LLC|Ltd\.?|Corp\.?|Corporation)?',
            r'[A-Z]{2,}',  # Acronyms like IBM, NASA
        ]
        
        # Date patterns
        self.date_patterns = [
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
            r'\d{1,2}[/-]\d{4}',
            r'\d{4}[/-]\d{4}',
            r'(?:Present|Current|Now)',
        ]
    
    def extract_experience(self, text: str) -> Dict[str, Any]:
        """
        Extract work experience from resume text
        
        Returns:
            Dictionary with extracted experience data
        """
        try:
            logger.info("Extracting work experience")
            
            # Find experience section
            experience_section = self._find_experience_section(text)
            
            if not experience_section:
                logger.warning("No experience section found")
                return {
                    'experiences': [],
                    'total_experience_months': 0,
                    'total_experience_years': 0,
                    'current_position': None
                }
            
            # Parse individual experiences
            experiences = self._parse_experiences(experience_section)
            
            # Calculate total experience
            total_months = sum(exp.get('duration_months', 0) for exp in experiences)
            total_years = total_months / 12.0
            
            # Find current position
            current_position = next(
                (exp for exp in experiences if exp.get('is_current', False)),
                None
            )
            
            return {
                'experiences': experiences,
                'total_experience_months': int(total_months),
                'total_experience_years': round(total_years, 1),
                'current_position': current_position,
                'experience_count': len(experiences)
            }
            
        except Exception as e:
            logger.error(f"Error extracting experience: {str(e)}", exc_info=True)
            return {
                'experiences': [],
                'total_experience_months': 0,
                'total_experience_years': 0,
                'current_position': None
            }
    
    def _find_experience_section(self, text: str) -> Optional[str]:
        """Find and extract experience section from resume"""
        # Patterns to find experience section
        patterns = [
            r'(?:Work\s+)?Experience[:\s]*\n(.*?)(?:\n\n[A-Z]|$)',
            r'Employment[:\s]*\n(.*?)(?:\n\n[A-Z]|$)',
            r'Professional\s+Experience[:\s]*\n(.*?)(?:\n\n[A-Z]|$)',
            r'Career[:\s]*\n(.*?)(?:\n\n[A-Z]|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        
        return None
    
    def _parse_experiences(self, experience_text: str) -> List[Dict[str, Any]]:
        """Parse individual work experiences"""
        experiences = []
        
        # Split by common delimiters (newlines, bullet points)
        # Look for patterns like: Job Title | Company | Date
        lines = experience_text.split('\n')
        
        current_exp = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new experience entry
            if self._is_experience_header(line):
                # Save previous experience
                if current_exp:
                    experiences.append(current_exp)
                
                # Start new experience
                current_exp = self._parse_experience_header(line)
            elif current_exp:
                # Add to current experience
                if self._is_achievement(line):
                    current_exp.setdefault('achievements', []).append(line)
                elif self._is_date_range(line):
                    dates = self._parse_date_range(line)
                    if dates:
                        current_exp.update(dates)
                else:
                    current_exp.setdefault('description', []).append(line)
        
        # Add last experience
        if current_exp:
            experiences.append(current_exp)
        
        # Post-process experiences
        for exp in experiences:
            self._enrich_experience(exp)
        
        return experiences
    
    def _is_experience_header(self, line: str) -> bool:
        """Check if line is an experience header (title, company, date)"""
        # Check for job title pattern
        for pattern in self.job_title_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        # Check for company pattern
        for pattern in self.company_patterns:
            if re.search(pattern, line):
                return True
        
        return False
    
    def _parse_experience_header(self, line: str) -> Dict[str, Any]:
        """Parse experience header line"""
        exp = {
            'job_title': None,
            'company': None,
            'start_date': None,
            'end_date': None,
            'is_current': False,
            'achievements': [],
            'description': []
        }
        
        # Try to extract job title
        for pattern in self.job_title_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                exp['job_title'] = match.group(0).strip()
                break
        
        # Try to extract company
        for pattern in self.company_patterns:
            matches = re.findall(pattern, line)
            if matches:
                # Filter out common false positives
                filtered = [m for m in matches if len(m) > 2 and m.lower() not in ['the', 'and', 'or']]
                if filtered:
                    exp['company'] = filtered[0].strip()
                    break
        
        # Try to extract dates
        dates = self._parse_date_range(line)
        if dates:
            exp.update(dates)
        
        return exp
    
    def _parse_date_range(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse date range from text"""
        # Pattern for date ranges
        date_range_patterns = [
            r'(\w+\s+\d{4})\s*[-–—]\s*(\w+\s+\d{4}|Present|Current|Now)',
            r'(\d{1,2}[/-]\d{4})\s*[-–—]\s*(\d{1,2}[/-]\d{4}|Present|Current|Now)',
            r'(\d{4})\s*[-–—]\s*(\d{4}|Present|Current|Now)',
        ]
        
        for pattern in date_range_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start_str = match.group(1)
                end_str = match.group(2)
                
                start_date = dateparser.parse(start_str)
                is_current = end_str.lower() in ['present', 'current', 'now']
                
                if is_current:
                    end_date = datetime.now()
                else:
                    end_date = dateparser.parse(end_str)
                
                if start_date and end_date:
                    return {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat() if not is_current else None,
                        'is_current': is_current
                    }
        
        return None
    
    def _is_achievement(self, line: str) -> bool:
        """Check if line describes an achievement"""
        achievement_indicators = [
            r'^[•\-\*]\s*',
            r'^[A-Z][a-z]+\s+(?:by|to|from|with)\s+',
            r'\d+%',
            r'\$\d+',
            r'(?:increased|decreased|improved|achieved|delivered|led|managed)',
        ]
        
        for pattern in achievement_indicators:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        return False
    
    def _enrich_experience(self, exp: Dict[str, Any]) -> None:
        """Enrich experience with calculated fields"""
        # Calculate duration
        if exp.get('start_date'):
            start = datetime.fromisoformat(exp['start_date'])
            if exp.get('is_current') or not exp.get('end_date'):
                end = datetime.now()
            else:
                end = datetime.fromisoformat(exp['end_date'])
            
            delta = end - start
            months = (delta.days / 30.44)  # Average days per month
            years = months / 12
            
            exp['duration_months'] = int(months)
            exp['duration_years'] = round(years, 1)
        
        # Clean up job title
        if exp.get('job_title'):
            exp['job_title'] = exp['job_title'].strip()
        
        # Clean up company
        if exp.get('company'):
            exp['company'] = exp['company'].strip()
        
        # Join description lines
        if exp.get('description'):
            exp['description'] = ' '.join(exp['description'])
        
        # Extract key achievements
        if exp.get('achievements'):
            exp['key_achievements'] = exp['achievements'][:5]  # Top 5


# Singleton instance
experience_parser = ExperienceParser()

