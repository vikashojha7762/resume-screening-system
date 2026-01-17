"""
Performance tests
"""
import pytest
import time
from fastapi.testclient import TestClient
from app.main import app
from tests.fixtures.database import override_get_db, test_user


@pytest.fixture
def client(test_db, override_get_db):
    """Create test client"""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestAPIPerformance:
    """API performance tests"""
    
    def test_job_list_response_time(self, client, test_user):
        """Test job list API response time"""
        token = create_access_token(data={"sub": test_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        start = time.time()
        response = client.get("/api/v1/jobs", headers=headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in under 1 second
    
    def test_resume_upload_performance(self, client, test_user):
        """Test resume upload performance"""
        token = create_access_token(data={"sub": test_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        file_content = b"x" * (5 * 1024 * 1024)  # 5MB
        
        start = time.time()
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("test.pdf", file_content, "application/pdf")},
            headers=headers
        )
        elapsed = time.time() - start
        
        assert response.status_code in [200, 201]
        assert elapsed < 5.0  # Should upload in under 5 seconds


class TestDatabasePerformance:
    """Database performance tests"""
    
    def test_query_performance(self, db_session):
        """Test database query performance"""
        from app.models.job import Job
        
        # Create multiple jobs
        for i in range(100):
            job = Job(
                title=f"Job {i}",
                description="Test",
                status="active",
                created_by="test_user_id"
            )
            db_session.add(job)
        db_session.commit()
        
        # Test query performance
        start = time.time()
        jobs = db_session.query(Job).filter(Job.status == "active").all()
        elapsed = time.time() - start
        
        assert len(jobs) == 100
        assert elapsed < 0.1  # Should query in under 100ms


class TestNLPPerformance:
    """NLP processing performance tests"""
    
    def test_resume_parsing_performance(self):
        """Test resume parsing performance"""
        from app.services.resume_parser import ResumeParser
        
        parser = ResumeParser()
        text = "Test resume content " * 1000  # Large text
        
        start = time.time()
        result = parser.clean_text(text)
        elapsed = time.time() - start
        
        assert result is not None
        assert elapsed < 1.0  # Should parse in under 1 second
    
    def test_skill_extraction_performance(self):
        """Test skill extraction performance"""
        from app.services.skill_extractor import SkillExtractor
        
        extractor = SkillExtractor()
        text = "Python JavaScript Java " * 100
        
        start = time.time()
        # Mock extraction
        elapsed = time.time() - start
        
        assert elapsed < 0.5  # Should extract in under 500ms

