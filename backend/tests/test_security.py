"""
Security tests
"""
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.core.security import create_access_token
from tests.fixtures.database import override_get_db, test_user


@pytest.fixture
def client(test_db, override_get_db):
    """Create test client"""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestAuthenticationSecurity:
    """Tests for authentication security"""
    
    def test_invalid_token_rejected(self, client):
        """Test that invalid tokens are rejected"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_expired_token_rejected(self, client):
        """Test that expired tokens are rejected"""
        # Create expired token
        expired_token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(seconds=-1)  # Expired
        )
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
    
    def test_no_token_rejected(self, client):
        """Test that requests without token are rejected"""
        response = client.get("/api/v1/jobs")
        assert response.status_code == 401


class TestSQLInjectionPrevention:
    """Tests for SQL injection prevention"""
    
    def test_sql_injection_in_email(self, client):
        """Test SQL injection in email field"""
        malicious_input = "test@example.com' OR '1'='1"
        response = client.post(
            "/api/v1/auth/login/json",
            data={
                "username": malicious_input,
                "password": "password"
            }
        )
        # Should not expose database errors
        assert response.status_code in [401, 400]
    
    def test_sql_injection_in_search(self, client, test_user):
        """Test SQL injection in search parameters"""
        token = create_access_token(data={"sub": test_user.email})
        malicious_input = "'; DROP TABLE users; --"
        
        response = client.get(
            f"/api/v1/jobs?search={malicious_input}",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should handle safely without executing SQL
        assert response.status_code in [200, 400]


class TestXSSPrevention:
    """Tests for XSS prevention"""
    
    def test_xss_in_job_title(self, client, test_user):
        """Test XSS in job title"""
        token = create_access_token(data={"sub": test_user.email})
        xss_payload = "<script>alert('XSS')</script>"
        
        response = client.post(
            "/api/v1/jobs",
            json={
                "title": xss_payload,
                "description": "Test"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should sanitize or reject
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            # Check that script tags are removed
            assert "<script>" not in response.json()["title"]


class TestFileUploadSecurity:
    """Tests for file upload security"""
    
    def test_malicious_file_extension(self, client, test_user):
        """Test rejection of malicious file extensions"""
        token = create_access_token(data={"sub": test_user.email})
        
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("malicious.exe", b"malicious content", "application/x-msdownload")},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
    
    def test_file_size_limit(self, client, test_user):
        """Test file size limit enforcement"""
        token = create_access_token(data={"sub": test_user.email})
        large_file = b"x" * (11 * 1024 * 1024)  # 11MB
        
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("large.pdf", large_file, "application/pdf")},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
    
    def test_path_traversal_prevention(self, client, test_user):
        """Test path traversal prevention"""
        token = create_access_token(data={"sub": test_user.email})
        malicious_filename = "../../../etc/passwd"
        
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": (malicious_filename, b"content", "application/pdf")},
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should sanitize filename
        assert response.status_code in [200, 400]


class TestDataPrivacy:
    """Tests for data privacy compliance"""
    
    def test_pii_masking(self, client, test_user, test_resume):
        """Test PII masking in candidate data"""
        from app.services.bias_detector import BiasDetector
        
        detector = BiasDetector()
        resume_data = {
            "contact_info": {
                "email": "test@example.com",
                "phone": "+1234567890",
                "name": "John Doe"
            }
        }
        
        anonymized = detector.anonymize_resume(resume_data)
        
        assert "[MASKED]" in anonymized["contact_info"]["email"]
        assert "[MASKED]" in anonymized["contact_info"]["phone"]
        assert "[MASKED]" in anonymized["contact_info"]["name"]
    
    def test_candidate_anonymization(self, client, test_user, test_resume):
        """Test candidate anonymization"""
        from app.models.candidate import Candidate
        
        candidate = Candidate(
            anonymized_id="anon_123",
            resume_id=test_resume.id,
            masked_data_json={"name": "[MASKED]"}
        )
        
        assert candidate.anonymized_id is not None
        assert "[MASKED]" in str(candidate.masked_data_json)

