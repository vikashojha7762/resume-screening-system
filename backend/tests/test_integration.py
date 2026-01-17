"""
Integration tests for end-to-end workflows
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.core.security import create_access_token
from tests.fixtures.database import test_db, override_get_db, test_user, test_job, test_resume


@pytest.fixture
def client(test_db, override_get_db):
    """Create test client"""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestResumeProcessingPipeline:
    """End-to-end resume processing pipeline tests"""
    
    @pytest.mark.asyncio
    async def test_complete_resume_processing(self, client, test_user, test_job):
        """Test complete resume processing workflow"""
        # 1. Upload resume
        file_content = b"PDF content"
        upload_response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("test.pdf", file_content, "application/pdf")},
            headers={"Authorization": f"Bearer {create_access_token({'sub': test_user.email})}"}
        )
        assert upload_response.status_code in [200, 201]
        resume_id = upload_response.json()["id"]
        
        # 2. Wait for processing (mock async task)
        # In real scenario, this would wait for Celery task
        
        # 3. Match job to candidates
        match_response = client.post(
            f"/api/v1/results/job/{test_job.id}/match",
            json={"strategy": "standard"},
            headers={"Authorization": f"Bearer {create_access_token({'sub': test_user.email})}"}
        )
        assert match_response.status_code in [200, 202]
        
        # 4. Get ranked results
        results_response = client.get(
            f"/api/v1/results/job/{test_job.id}/ranked",
            headers={"Authorization": f"Bearer {create_access_token({'sub': test_user.email})}"}
        )
        assert results_response.status_code == 200


class TestDatabaseIntegration:
    """Database integration tests"""
    
    def test_database_transaction_rollback(self, db_session, test_user):
        """Test database transaction rollback"""
        from app.models.job import Job
        
        job = Job(
            title="Test Job",
            description="Test",
            status="draft",
            created_by=test_user.id
        )
        db_session.add(job)
        db_session.flush()
        
        job_id = job.id
        assert job_id is not None
        
        # Rollback
        db_session.rollback()
        
        # Job should not exist after rollback
        result = db_session.query(Job).filter(Job.id == job_id).first()
        assert result is None
    
    def test_database_relationships(self, db_session, test_user, test_resume):
        """Test database relationships"""
        from app.models.candidate import Candidate
        
        candidate = Candidate(
            anonymized_id="anon_123",
            resume_id=test_resume.id
        )
        db_session.add(candidate)
        db_session.commit()
        
        # Test relationship
        assert candidate.resume.id == test_resume.id
        assert candidate.resume.file_name == test_resume.file_name


class TestExternalServiceIntegration:
    """Tests for external service integrations"""
    
    @pytest.mark.skipif(True, reason="Requires AWS credentials")
    def test_s3_integration(self, mock_s3_client):
        """Test S3 integration"""
        from app.services.file_service import FileService
        
        service = FileService()
        result = service.upload_to_s3(
            file_content=b"test content",
            bucket="test-bucket",
            key="test/key.pdf"
        )
        assert result is not None
    
    @pytest.mark.skipif(True, reason="Requires email configuration")
    def test_email_integration(self, mock_email_service):
        """Test email service integration"""
        # Email sending would be tested here
        pass


class TestAuthenticationFlow:
    """Tests for authentication flow"""
    
    def test_complete_auth_flow(self, client):
        """Test complete authentication flow"""
        # 1. Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123"
            }
        )
        assert register_response.status_code == 200
        
        # 2. Login
        login_response = client.post(
            "/api/v1/auth/login/json",
            data={
                "username": "newuser@example.com",
                "password": "password123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 3. Access protected endpoint
        protected_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert protected_response.status_code == 200
        assert protected_response.json()["email"] == "newuser@example.com"

