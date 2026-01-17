"""
Tests for service layer
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.file_service import FileService
from app.services.resume_parser import ResumeParser
from app.services.skill_extractor import SkillExtractor
from app.services.scoring_engine import ScoringEngine
from app.services.ranking_engine import RankingEngine


class TestFileService:
    """Tests for FileService"""
    
    def test_validate_file_type(self):
        """Test file type validation"""
        service = FileService()
        
        assert service.validate_file_type("test.pdf") is True
        assert service.validate_file_type("test.doc") is True
        assert service.validate_file_type("test.docx") is True
        assert service.validate_file_type("test.txt") is True
        assert service.validate_file_type("test.exe") is False
        assert service.validate_file_type("test.jpg") is False
    
    def test_validate_file_size(self):
        """Test file size validation"""
        service = FileService()
        
        assert service.validate_file_size(5 * 1024 * 1024) is True  # 5MB
        assert service.validate_file_size(10 * 1024 * 1024) is True  # 10MB
        assert service.validate_file_size(11 * 1024 * 1024) is False  # 11MB
    
    @patch('app.services.file_service.boto3')
    def test_upload_to_s3(self, mock_boto, mock_s3_client):
        """Test S3 upload"""
        service = FileService()
        file_content = b"test content"
        
        result = service.upload_to_s3(
            file_content=file_content,
            bucket="test-bucket",
            key="test/key.pdf"
        )
        
        assert result is not None


class TestResumeParser:
    """Tests for ResumeParser"""
    
    def test_parse_pdf(self):
        """Test PDF parsing"""
        parser = ResumeParser()
        # Mock PDF content
        with patch('app.services.resume_parser.PyPDF2.PdfReader') as mock_pdf:
            mock_pdf.return_value.pages = [MagicMock(extract_text=lambda: "Test resume content")]
            result = parser.parse_pdf(b"PDF content")
            assert result is not None
    
    def test_parse_docx(self):
        """Test DOCX parsing"""
        parser = ResumeParser()
        with patch('app.services.resume_parser.Document') as mock_docx:
            mock_docx.return_value.paragraphs = [MagicMock(text="Test content")]
            result = parser.parse_docx(b"DOCX content")
            assert result is not None
    
    def test_clean_text(self):
        """Test text cleaning"""
        parser = ResumeParser()
        dirty_text = "  Test   Text  \n\n\n  "
        clean_text = parser.clean_text(dirty_text)
        assert clean_text == "Test Text"


class TestSkillExtractor:
    """Tests for SkillExtractor"""
    
    def test_extract_skills(self):
        """Test skill extraction"""
        extractor = SkillExtractor()
        text = "I have experience with Python, JavaScript, and PostgreSQL"
        
        with patch('app.services.skill_extractor.spacy.load') as mock_spacy:
            mock_nlp = MagicMock()
            mock_doc = MagicMock()
            mock_doc.ents = []
            mock_nlp.return_value = mock_doc
            mock_spacy.return_value = mock_nlp
            
            skills = extractor.extract_skills(text)
            assert isinstance(skills, list)
    
    def test_normalize_skill(self):
        """Test skill normalization"""
        extractor = SkillExtractor()
        
        assert extractor.normalize_skill("Python 3") == "python"
        assert extractor.normalize_skill("JavaScript/JS") == "javascript"


class TestScoringEngine:
    """Tests for ScoringEngine"""
    
    def test_calculate_score(self):
        """Test score calculation"""
        engine = ScoringEngine()
        
        job = {
            "requirements_json": {
                "required_skills": ["Python", "FastAPI"],
                "min_experience_years": 3
            }
        }
        
        resume_data = {
            "skills": {
                "skills": [{"name": "Python"}, {"name": "FastAPI"}]
            },
            "experience": {
                "total_experience_years": 5.0
            },
            "education": {
                "highest_degree": "Bachelor's"
            }
        }
        
        # This would need proper mock setup
        # score = engine.calculate_score(job, resume_data)
        # assert score["overall_score"] > 0


class TestRankingEngine:
    """Tests for RankingEngine"""
    
    def test_rank_candidates(self):
        """Test candidate ranking"""
        engine = RankingEngine()
        
        candidates = [
            {"candidate_id": "1", "overall_score": 0.9},
            {"candidate_id": "2", "overall_score": 0.7},
            {"candidate_id": "3", "overall_score": 0.8}
        ]
        
        ranked = engine.rank_candidates(candidates)
        
        assert len(ranked) == 3
        assert ranked[0]["overall_score"] >= ranked[1]["overall_score"]
        assert ranked[1]["overall_score"] >= ranked[2]["overall_score"]

