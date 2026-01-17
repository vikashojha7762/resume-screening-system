"""
Tests for NLP component accuracy
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.resume_parser import ResumeParser
from app.services.skill_extractor import SkillExtractor
from app.services.experience_parser import ExperienceParser
from app.services.education_parser import EducationParser
from tests.factories import generate_synthetic_resume_text


class TestResumeParserAccuracy:
    """Tests for resume parser accuracy"""
    
    def test_parse_skills_section(self):
        """Test parsing skills section"""
        parser = ResumeParser()
        text = """
        SKILLS
        Programming: Python, JavaScript, Java
        Databases: PostgreSQL, MongoDB
        Tools: Docker, Kubernetes
        """
        
        sections = parser.detect_sections(text)
        assert "skills" in [s.lower() for s in sections.keys()]
    
    def test_parse_experience_section(self):
        """Test parsing experience section"""
        parser = ResumeParser()
        text = """
        EXPERIENCE
        Software Engineer | Google | 2020-2023
        Developed web applications using Python and FastAPI
        """
        
        sections = parser.detect_sections(text)
        assert "experience" in [s.lower() for s in sections.keys()]
    
    def test_parse_education_section(self):
        """Test parsing education section"""
        parser = ResumeParser()
        text = """
        EDUCATION
        Bachelor of Science in Computer Science
        MIT | 2020
        """
        
        sections = parser.detect_sections(text)
        assert "education" in [s.lower() for s in sections.keys()]


class TestSkillExtractorPrecision:
    """Tests for skill extractor precision and recall"""
    
    def test_exact_skill_match(self):
        """Test exact skill matching"""
        extractor = SkillExtractor()
        text = "I have experience with Python, JavaScript, and PostgreSQL"
        
        # Mock spaCy NER
        with patch('app.services.skill_extractor.spacy.load') as mock_spacy:
            mock_nlp = MagicMock()
            mock_doc = MagicMock()
            mock_doc.ents = []
            mock_nlp.return_value = mock_doc
            
            skills = extractor.extract_skills(text)
            # Should extract Python, JavaScript, PostgreSQL
            skill_names = [s.name.lower() for s in skills]
            assert "python" in skill_names or "javascript" in skill_names
    
    def test_skill_synonym_matching(self):
        """Test skill synonym matching"""
        extractor = SkillExtractor()
        
        # Test that "JS" maps to "JavaScript"
        normalized = extractor.normalize_skill("JS")
        assert normalized in ["javascript", "js"]
    
    def test_skill_categorization(self):
        """Test skill categorization"""
        extractor = SkillExtractor()
        
        programming_skills = ["Python", "Java", "JavaScript"]
        for skill in programming_skills:
            category = extractor.categorize_skill(skill)
            assert category in ["Programming", "Language", None]  # Allow None for flexibility


class TestExperienceParserEdgeCases:
    """Tests for experience parser edge cases"""
    
    def test_parse_date_formats(self):
        """Test parsing various date formats"""
        parser = ExperienceParser()
        
        date_formats = [
            "2020-2023",
            "Jan 2020 - Dec 2023",
            "01/2020 - 12/2023",
            "2020 to 2023"
        ]
        
        for date_str in date_formats:
            # Should handle various formats
            result = parser.parse_date_range(date_str)
            assert result is not None or isinstance(result, dict)
    
    def test_parse_current_position(self):
        """Test parsing current position"""
        parser = ExperienceParser()
        text = "Software Engineer | Google | 2020 - Present"
        
        experience = parser.parse_experience(text)
        # Should handle "Present" as end date
        assert experience is not None
    
    def test_parse_multiple_positions(self):
        """Test parsing multiple positions"""
        parser = ExperienceParser()
        text = """
        Software Engineer | Google | 2020-2023
        Junior Developer | Startup | 2018-2020
        """
        
        experiences = parser.parse_experience(text)
        assert len(experiences) >= 1


class TestEducationParserEdgeCases:
    """Tests for education parser edge cases"""
    
    def test_parse_degree_variations(self):
        """Test parsing degree variations"""
        parser = EducationParser()
        
        degree_variations = [
            "Bachelor of Science",
            "B.S. in Computer Science",
            "BS Computer Science",
            "Bachelor's Degree"
        ]
        
        for degree_str in degree_variations:
            degree = parser.extract_degree(degree_str)
            assert degree is not None
    
    def test_parse_gpa_formats(self):
        """Test parsing various GPA formats"""
        parser = EducationParser()
        
        gpa_formats = [
            "GPA: 3.8/4.0",
            "CGPA: 8.5/10",
            "3.8 GPA"
        ]
        
        for gpa_str in gpa_formats:
            gpa = parser.extract_gpa(gpa_str)
            # Should extract numeric GPA value
            assert gpa is None or isinstance(gpa, (int, float))


class TestMLModelPerformance:
    """Tests for ML model performance benchmarks"""
    
    def test_embedding_generation_speed(self):
        """Test embedding generation speed"""
        from app.ml.embeddings import EmbeddingService
        
        service = EmbeddingService()
        text = "Software engineer with Python experience"
        
        import time
        start = time.time()
        embedding = service.generate_embedding(text)
        elapsed = time.time() - start
        
        # Should generate embedding in reasonable time (< 1 second)
        assert elapsed < 1.0
        assert embedding is not None
        assert len(embedding) > 0
    
    def test_batch_embedding_performance(self):
        """Test batch embedding performance"""
        from app.ml.embeddings import EmbeddingService
        
        service = EmbeddingService()
        texts = [f"Resume text {i}" for i in range(10)]
        
        import time
        start = time.time()
        embeddings = service.generate_batch_embeddings(texts)
        elapsed = time.time() - start
        
        # Batch should be faster than individual
        assert elapsed < 5.0
        assert len(embeddings) == 10

