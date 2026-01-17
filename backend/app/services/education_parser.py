"""
Education Parser Service
Extracts education information including degrees, institutions, GPA, and graduation year
"""
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EducationParser:
    """Parse education information from resume text"""
    
    def __init__(self):
        # Degree patterns
        self.degree_patterns = {
            'phd': [
                r'Ph\.?D\.?',
                r'Doctor of Philosophy',
                r'Doctorate',
            ],
            'masters': [
                r'M\.?S\.?',
                r'M\.?Sc\.?',
                r'Master of Science',
                r'Master of Arts',
                r'M\.?A\.?',
                r'M\.?B\.?A\.?',
                r'Master of Business Administration',
                r'M\.?E\.?ng\.?',
                r'Master of Engineering',
            ],
            'bachelors': [
                r'B\.?S\.?',
                r'B\.?Sc\.?',
                r'Bachelor of Science',
                r'Bachelor of Arts',
                r'B\.?A\.?',
                r'B\.?E\.?ng\.?',
                r'Bachelor of Engineering',
                r'B\.?T\.?ech\.?',
                r'Bachelor of Technology',
            ],
            'associates': [
                r'A\.?A\.?',
                r'A\.?S\.?',
                r'Associate of Arts',
                r'Associate of Science',
            ],
            'diploma': [
                r'Diploma',
                r'Certificate',
            ]
        }
        
        # Field of study patterns
        self.field_patterns = [
            r'in\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z\s]+)\s+(?:Engineering|Science|Arts|Studies)',
        ]
        
        # GPA patterns
        self.gpa_patterns = [
            r'GPA[:\s]*(\d+\.?\d*)',
            r'CGPA[:\s]*(\d+\.?\d*)',
            r'Grade[:\s]*(\d+\.?\d*)',
        ]
    
    def extract_education(self, text: str) -> Dict[str, Any]:
        """
        Extract education information from resume text
        
        Returns:
            Dictionary with extracted education data
        """
        try:
            logger.info("Extracting education information")
            
            # Find education section
            education_section = self._find_education_section(text)
            
            if not education_section:
                logger.warning("No education section found")
                return {
                    'educations': [],
                    'highest_degree': None,
                    'total_degrees': 0
                }
            
            # Parse individual education entries
            educations = self._parse_educations(education_section)
            
            # Determine highest degree
            highest_degree = self._get_highest_degree(educations)
            
            return {
                'educations': educations,
                'highest_degree': highest_degree,
                'total_degrees': len(educations)
            }
            
        except Exception as e:
            logger.error(f"Error extracting education: {str(e)}", exc_info=True)
            return {
                'educations': [],
                'highest_degree': None,
                'total_degrees': 0
            }
    
    def _find_education_section(self, text: str) -> Optional[str]:
        """Find and extract education section from resume"""
        patterns = [
            r'Education[:\s]*\n(.*?)(?:\n\n[A-Z]|$)',
            r'Academic[:\s]*\n(.*?)(?:\n\n[A-Z]|$)',
            r'Qualifications[:\s]*\n(.*?)(?:\n\n[A-Z]|$)',
            r'Degrees?[:\s]*\n(.*?)(?:\n\n[A-Z]|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        
        return None
    
    def _parse_educations(self, education_text: str) -> List[Dict[str, Any]]:
        """Parse individual education entries"""
        educations = []
        
        lines = education_text.split('\n')
        current_edu = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new education entry
            if self._is_education_header(line):
                # Save previous education
                if current_edu:
                    educations.append(current_edu)
                
                # Start new education
                current_edu = self._parse_education_header(line)
            elif current_edu:
                # Add to current education
                if self._is_gpa_line(line):
                    gpa = self._extract_gpa(line)
                    if gpa:
                        current_edu['gpa'] = gpa
                elif self._is_year_line(line):
                    year = self._extract_year(line)
                    if year:
                        current_edu['graduation_year'] = year
                else:
                    # Could be institution or field of study
                    if not current_edu.get('institution'):
                        current_edu['institution'] = line
                    elif not current_edu.get('field_of_study'):
                        current_edu['field_of_study'] = line
        
        # Add last education
        if current_edu:
            educations.append(current_edu)
        
        # Post-process educations
        for edu in educations:
            self._enrich_education(edu)
        
        return educations
    
    def _is_education_header(self, line: str) -> bool:
        """Check if line is an education header"""
        # Check for degree pattern
        for degree_type, patterns in self.degree_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    return True
        
        return False
    
    def _parse_education_header(self, line: str) -> Dict[str, Any]:
        """Parse education header line"""
        edu = {
            'degree': None,
            'degree_type': None,
            'institution': None,
            'field_of_study': None,
            'graduation_year': None,
            'gpa': None,
        }
        
        # Extract degree
        for degree_type, patterns in self.degree_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    edu['degree'] = match.group(0).strip()
                    edu['degree_type'] = degree_type
                    break
            if edu['degree']:
                break
        
        # Extract field of study
        for pattern in self.field_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                edu['field_of_study'] = match.group(1).strip()
                break
        
        # Extract year
        year = self._extract_year(line)
        if year:
            edu['graduation_year'] = year
        
        # Extract GPA
        gpa = self._extract_gpa(line)
        if gpa:
            edu['gpa'] = gpa
        
        return edu
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract graduation year"""
        # Look for 4-digit years (1900-2100)
        year_pattern = r'\b(19|20)\d{2}\b'
        matches = re.findall(year_pattern, text)
        
        if matches:
            # Return the most recent year
            years = [int(match[0] + match[1]) for match in matches if len(match) == 2]
            if years:
                return max(years)
        
        return None
    
    def _extract_gpa(self, text: str) -> Optional[float]:
        """Extract GPA/CGPA"""
        for pattern in self.gpa_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    gpa = float(match.group(1))
                    # Normalize to 4.0 scale if needed
                    if gpa > 4.0 and gpa <= 10.0:
                        gpa = (gpa / 10.0) * 4.0
                    return round(gpa, 2)
                except ValueError:
                    continue
        
        return None
    
    def _is_gpa_line(self, line: str) -> bool:
        """Check if line contains GPA information"""
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in self.gpa_patterns)
    
    def _is_year_line(self, line: str) -> bool:
        """Check if line contains year information"""
        return bool(re.search(r'\b(19|20)\d{2}\b', line))
    
    def _enrich_education(self, edu: Dict[str, Any]) -> None:
        """Enrich education with calculated fields"""
        # Clean up degree
        if edu.get('degree'):
            edu['degree'] = edu['degree'].strip()
        
        # Clean up institution
        if edu.get('institution'):
            edu['institution'] = edu['institution'].strip()
        
        # Clean up field of study
        if edu.get('field_of_study'):
            edu['field_of_study'] = edu['field_of_study'].strip()
        
        # Calculate years since graduation
        if edu.get('graduation_year'):
            current_year = datetime.now().year
            years_since = current_year - edu['graduation_year']
            edu['years_since_graduation'] = years_since
    
    def _get_highest_degree(self, educations: List[Dict[str, Any]]) -> Optional[str]:
        """Determine highest degree level"""
        degree_hierarchy = {
            'phd': 5,
            'masters': 4,
            'bachelors': 3,
            'associates': 2,
            'diploma': 1,
        }
        
        highest_level = 0
        highest_degree = None
        
        for edu in educations:
            degree_type = edu.get('degree_type')
            if degree_type and degree_hierarchy.get(degree_type, 0) > highest_level:
                highest_level = degree_hierarchy[degree_type]
                highest_degree = edu.get('degree')
        
        return highest_degree


# Singleton instance
education_parser = EducationParser()

