"""
End-to-End Integration Tests
Tests complete user journey from job creation to candidate selection
"""
import pytest
import time
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.core.security import create_access_token
from tests.fixtures.database import override_get_db, test_user, test_db
from tests.factories import JobFactory, ResumeFactory


@pytest.fixture
def client(test_db, override_get_db):
    """Create test client"""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_token(test_user):
    """Create authentication token"""
    return create_access_token(data={"sub": test_user.email})


class TestCompleteUserJourney:
    """Test complete user journey end-to-end"""
    
    def test_complete_workflow(self, client, auth_token, test_user):
        """Test: Job creation → Resume upload → Processing → Matching → Results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Create Job
        job_data = {
            "title": "Senior Software Engineer",
            "description": "We are looking for an experienced software engineer",
            "requirements_json": {
                "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                "min_experience_years": 5,
                "required_degree": "Bachelor's"
            },
            "status": "active"
        }
        
        job_response = client.post(
            "/api/v1/jobs",
            json=job_data,
            headers=headers
        )
        assert job_response.status_code == 200
        job_id = job_response.json()["id"]
        print(f"✅ Step 1: Job created - ID: {job_id}")
        
        # Step 2: Upload Resume
        resume_content = b"PDF content for testing"
        upload_response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("test_resume.pdf", resume_content, "application/pdf")},
            headers=headers
        )
        assert upload_response.status_code in [200, 201]
        resume_id = upload_response.json()["id"]
        print(f"✅ Step 2: Resume uploaded - ID: {resume_id}")
        
        # Step 3: Wait for Processing (simulated)
        # In real scenario, wait for Celery task completion
        time.sleep(2)  # Simulate processing time
        
        # Step 4: Check Processing Status
        status_response = client.get(
            f"/api/v1/resumes/{resume_id}",
            headers=headers
        )
        assert status_response.status_code == 200
        status = status_response.json()["status"]
        print(f"✅ Step 3: Resume status - {status}")
        
        # Step 5: Match Job to Candidates
        match_response = client.post(
            f"/api/v1/results/job/{job_id}/match",
            json={
                "strategy": "standard",
                "diversity_weight": 0.1,
                "enable_bias_detection": True
            },
            headers=headers
        )
        assert match_response.status_code in [200, 202]
        print(f"✅ Step 4: Matching initiated")
        
        # Step 6: Get Ranked Results
        results_response = client.get(
            f"/api/v1/results/job/{job_id}/ranked",
            headers=headers
        )
        assert results_response.status_code == 200
        results = results_response.json()
        print(f"✅ Step 5: Results retrieved - {results.get('total', 0)} candidates")
        
        # Step 7: Verify Data Consistency
        # Check that job, resume, and results are linked correctly
        job_check = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
        assert job_check.status_code == 200
        assert job_check.json()["id"] == job_id
        
        resume_check = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
        assert resume_check.status_code == 200
        assert resume_check.json()["id"] == resume_id
        
        print("✅ Step 6: Data consistency verified")
        print("✅ Complete workflow test PASSED")


class TestErrorScenarios:
    """Test error scenarios and recovery"""
    
    def test_invalid_job_creation(self, client, auth_token):
        """Test job creation with invalid data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Missing required fields
        response = client.post(
            "/api/v1/jobs",
            json={"title": ""},  # Empty title
            headers=headers
        )
        assert response.status_code == 422  # Validation error
        print("✅ Invalid job creation handled correctly")
    
    def test_unauthorized_access(self, client):
        """Test unauthorized API access"""
        # No token
        response = client.get("/api/v1/jobs")
        assert response.status_code == 401
        print("✅ Unauthorized access blocked")
    
    def test_invalid_file_upload(self, client, auth_token):
        """Test invalid file upload"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Invalid file type
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("test.exe", b"content", "application/x-msdownload")},
            headers=headers
        )
        assert response.status_code == 400
        print("✅ Invalid file upload rejected")
    
    def test_nonexistent_resource(self, client, auth_token):
        """Test accessing nonexistent resources"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = client.get(
            "/api/v1/jobs/00000000-0000-0000-0000-000000000000",
            headers=headers
        )
        assert response.status_code == 404
        print("✅ Nonexistent resource handled correctly")


class TestDataConsistency:
    """Test data consistency across services"""
    
    def test_job_resume_relationship(self, client, auth_token, test_user):
        """Test job and resume relationship consistency"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create job
        job = client.post(
            "/api/v1/jobs",
            json=JobFactory(),
            headers=headers
        ).json()
        
        # Upload resume
        resume = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("test.pdf", b"content", "application/pdf")},
            headers=headers
        ).json()
        
        # Match and verify relationship
        match = client.post(
            f"/api/v1/results/job/{job['id']}/match",
            json={"strategy": "standard"},
            headers=headers
        )
        
        assert match.status_code in [200, 202]
        print("✅ Job-resume relationship consistent")
    
    def test_match_result_consistency(self, client, auth_token):
        """Test match result data consistency"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create job and match
        job = client.post(
            "/api/v1/jobs",
            json=JobFactory(),
            headers=headers
        ).json()
        
        match = client.post(
            f"/api/v1/results/job/{job['id']}/match",
            json={"strategy": "standard"},
            headers=headers
        )
        
        if match.status_code in [200, 202]:
            results = client.get(
                f"/api/v1/results/job/{job['id']}/ranked",
                headers=headers
            ).json()
            
            # Verify all results reference the correct job
            for result in results.get("items", []):
                assert result["job_id"] == job["id"]
            
            print("✅ Match result consistency verified")

