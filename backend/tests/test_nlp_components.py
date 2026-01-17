"""
Tests for NLP components
"""
import pytest
from app.services.resume_parser import resume_parser
from app.services.skill_extractor import skill_extractor
from app.services.experience_parser import experience_parser
from app.services.education_parser import education_parser
from app.services.nlp_pipeline import nlp_pipeline


def test_resume_parser_text_extraction():
    """Test text extraction from plain text"""
    text_content = b"This is a sample resume text.\nIt contains multiple lines."
    
    result = resume_parser.parse(text_content, 'txt', 'test.txt')
    
    assert 'raw_text' in result
    assert 'word_count' in result
    assert result['word_count'] > 0


def test_contact_info_extraction():
    """Test contact information extraction"""
    text = """
    John Doe
    Email: john.doe@example.com
    Phone: +1-555-123-4567
    LinkedIn: linkedin.com/in/johndoe
    """
    
    contact = resume_parser.extract_contact_info(text)
    
    assert contact['email'] == 'john.doe@example.com'
    assert contact['phone'] is not None
    assert contact['linkedin'] is not None


def test_skill_extraction():
    """Test skill extraction"""
    text = """
    Skills:
    Python, JavaScript, React, Node.js, PostgreSQL, AWS, Docker, Kubernetes
    """
    
    skills_data = skill_extractor.extract_skills(text)
    
    assert 'skills' in skills_data
    assert len(skills_data['skills']) > 0
    assert 'python' in [s.lower() for s in skills_data['skills']]


def test_experience_extraction():
    """Test work experience extraction"""
    text = """
    Work Experience:
    
    Software Engineer | Google | Jan 2020 - Present
    - Developed web applications
    - Led team of 5 developers
    
    Junior Developer | Microsoft | Jun 2018 - Dec 2019
    - Worked on backend systems
    """
    
    experience_data = experience_parser.extract_experience(text)
    
    assert 'experiences' in experience_data
    assert len(experience_data['experiences']) > 0
    assert experience_data['total_experience_months'] > 0


def test_education_extraction():
    """Test education extraction"""
    text = """
    Education:
    
    B.S. Computer Science
    MIT
    2018
    GPA: 3.8
    """
    
    education_data = education_parser.extract_education(text)
    
    assert 'educations' in education_data
    assert len(education_data['educations']) > 0
    assert education_data['highest_degree'] is not None


def test_nlp_pipeline_integration():
    """Test complete NLP pipeline"""
    text_content = b"""
    John Doe
    Email: john@example.com
    
    Skills: Python, JavaScript, React
    
    Experience:
    Software Engineer | Google | 2020 - Present
    
    Education:
    B.S. Computer Science | MIT | 2018
    """
    
    result = nlp_pipeline.process_resume(
        file_content=text_content,
        file_type='txt',
        filename='test_resume.txt',
        generate_embeddings=False  # Skip embeddings for faster tests
    )
    
    assert result['success'] is True
    assert 'contact_info' in result
    assert 'skills' in result
    assert 'experience' in result
    assert 'education' in result
    assert 'quality_metrics' in result

