"""
Tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from tests.fixtures.database import override_get_db, test_user, test_job, test_resume


@pytest.fixture
def client(test_db, override_get_db):
    """Create test client"""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers"""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


class TestAuthEndpoints:
    """Tests for authentication endpoints"""
    
    def test_register_user(self, client):
        """Test user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        assert "email" in response.json()
    
    def test_login_user(self, client, test_user):
        """Test user login"""
        response = client.post(
            "/api/v1/auth/login/json",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login/json",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user"""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "email" in response.json()


class TestJobEndpoints:
    """Tests for job endpoints"""
    
    def test_create_job(self, client, auth_headers):
        """Test creating a job"""
        response = client.post(
            "/api/v1/jobs",
            json={
                "title": "Test Job",
                "description": "Test description",
                "requirements_json": {
                    "required_skills": ["Python"]
                },
                "status": "draft"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Test Job"
    
    def test_get_jobs(self, client, auth_headers, test_job):
        """Test getting jobs list"""
        response = client.get(
            "/api/v1/jobs",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) > 0
    
    def test_get_job(self, client, auth_headers, test_job):
        """Test getting a single job"""
        response = client.get(
            f"/api/v1/jobs/{test_job.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(test_job.id)
    
    def test_update_job(self, client, auth_headers, test_job):
        """Test updating a job"""
        response = client.put(
            f"/api/v1/jobs/{test_job.id}",
            json={
                "title": "Updated Job Title"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Job Title"
    
    def test_delete_job(self, client, auth_headers, test_job):
        """Test deleting a job"""
        response = client.delete(
            f"/api/v1/jobs/{test_job.id}",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestResumeEndpoints:
    """Tests for resume endpoints"""
    
    def test_upload_resume(self, client, auth_headers):
        """Test uploading a resume"""
        file_content = b"PDF content"
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("test.pdf", file_content, "application/pdf")},
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
    
    def test_get_resumes(self, client, auth_headers, test_resume):
        """Test getting resumes list"""
        response = client.get(
            "/api/v1/resumes",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) > 0
    
    def test_delete_resume(self, client, auth_headers, test_resume):
        """Test deleting a resume"""
        response = client.delete(
            f"/api/v1/resumes/{test_resume.id}",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestResultsEndpoints:
    """Tests for results endpoints"""
    
    def test_get_ranked_results(self, client, auth_headers, test_job):
        """Test getting ranked results"""
        response = client.get(
            f"/api/v1/results/job/{test_job.id}/ranked",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_match_job_to_candidates(self, client, auth_headers, test_job):
        """Test matching job to candidates"""
        response = client.post(
            f"/api/v1/results/job/{test_job.id}/match",
            json={
                "strategy": "standard",
                "diversity_weight": 0.1
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 202]

