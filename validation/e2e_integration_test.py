"""
End-to-End Integration Test Suite
Tests complete user journey from job creation to candidate selection
"""
import pytest
import requests
import time
from typing import Dict, Any
import json


class TestE2EIntegration:
    """End-to-end integration tests"""
    
    BASE_URL = "http://localhost:8000/api/v1"
    TEST_USER = {
        "email": "e2e_test@example.com",
        "password": "TestPassword123!"
    }
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        # Register user
        response = requests.post(
            f"{self.BASE_URL}/auth/register",
            json=self.TEST_USER
        )
        
        # Login
        response = requests.post(
            f"{self.BASE_URL}/auth/login/json",
            data={
                "username": self.TEST_USER["email"],
                "password": self.TEST_USER["password"]
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get request headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_complete_user_journey(self, headers):
        """Test complete user journey: job → resume → match → results"""
        
        # Step 1: Create Job
        job_data = {
            "title": "Senior Software Engineer - E2E Test",
            "description": "We are looking for an experienced software engineer with Python and FastAPI experience.",
            "requirements_json": {
                "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                "preferred_skills": ["Docker", "Kubernetes"],
                "min_experience_years": 5,
                "required_degree": "Bachelor's"
            },
            "status": "active"
        }
        
        job_response = requests.post(
            f"{self.BASE_URL}/jobs",
            json=job_data,
            headers=headers
        )
        assert job_response.status_code == 200
        job_id = job_response.json()["id"]
        print(f"✅ Job created: {job_id}")
        
        # Step 2: Upload Resume
        resume_content = b"""
        John Doe
        Software Engineer
        
        SKILLS
        Python, FastAPI, PostgreSQL, Docker, Kubernetes
        
        EXPERIENCE
        Senior Software Engineer | Tech Corp | 2019-2024
        - Developed microservices using Python and FastAPI
        - Managed PostgreSQL databases
        - Deployed applications using Docker and Kubernetes
        
        Software Engineer | Startup Inc | 2015-2019
        - Built REST APIs
        - Database design and optimization
        
        EDUCATION
        Bachelor of Science in Computer Science
        University | 2015
        """
        
        resume_response = requests.post(
            f"{self.BASE_URL}/resumes/upload",
            files={"file": ("test_resume.txt", resume_content, "text/plain")},
            headers=headers
        )
        assert resume_response.status_code in [200, 201]
        resume_id = resume_response.json()["id"]
        print(f"✅ Resume uploaded: {resume_id}")
        
        # Step 3: Wait for Processing
        max_wait = 300  # 5 minutes
        wait_interval = 10  # Check every 10 seconds
        elapsed = 0
        
        while elapsed < max_wait:
            status_response = requests.get(
                f"{self.BASE_URL}/resumes/{resume_id}",
                headers=headers
            )
            status = status_response.json()["status"]
            
            if status == "processed":
                print(f"✅ Resume processed in {elapsed} seconds")
                break
            elif status == "error":
                pytest.fail("Resume processing failed")
            
            time.sleep(wait_interval)
            elapsed += wait_interval
        
        assert elapsed < max_wait, "Resume processing timeout"
        
        # Step 4: Match Job to Candidates
        match_response = requests.post(
            f"{self.BASE_URL}/results/job/{job_id}/match",
            json={
                "strategy": "standard",
                "diversity_weight": 0.1,
                "enable_bias_detection": True
            },
            headers=headers
        )
        assert match_response.status_code in [200, 202]
        print("✅ Matching initiated")
        
        # Step 5: Get Ranked Results
        results_response = requests.get(
            f"{self.BASE_URL}/results/job/{job_id}/ranked",
            headers=headers
        )
        assert results_response.status_code == 200
        results = results_response.json()
        
        assert "items" in results
        assert len(results["items"]) > 0
        print(f"✅ Found {len(results['items'])} matched candidates")
        
        # Step 6: Verify Result Quality
        top_candidate = results["items"][0]
        assert "overall_score" in top_candidate
        assert top_candidate["overall_score"] > 0
        print(f"✅ Top candidate score: {top_candidate['overall_score']}")
        
        return {
            "job_id": job_id,
            "resume_id": resume_id,
            "candidates_matched": len(results["items"]),
            "top_score": top_candidate["overall_score"]
        }
    
    def test_error_scenarios(self, headers):
        """Test error scenarios and recovery"""
        
        # Test 1: Invalid job ID
        response = requests.get(
            f"{self.BASE_URL}/jobs/invalid-id",
            headers=headers
        )
        assert response.status_code == 404
        
        # Test 2: Invalid file type
        response = requests.post(
            f"{self.BASE_URL}/resumes/upload",
            files={"file": ("test.exe", b"malicious content", "application/x-msdownload")},
            headers=headers
        )
        assert response.status_code == 400
        
        # Test 3: File too large
        large_file = b"x" * (11 * 1024 * 1024)  # 11MB
        response = requests.post(
            f"{self.BASE_URL}/resumes/upload",
            files={"file": ("large.pdf", large_file, "application/pdf")},
            headers=headers
        )
        assert response.status_code == 400
        
        # Test 4: Invalid authentication
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(
            f"{self.BASE_URL}/jobs",
            headers=invalid_headers
        )
        assert response.status_code == 401
        
        print("✅ All error scenarios handled correctly")
    
    def test_data_consistency(self, headers):
        """Test data consistency across services"""
        
        # Create job
        job_response = requests.post(
            f"{self.BASE_URL}/jobs",
            json={
                "title": "Test Job",
                "description": "Test",
                "status": "active"
            },
            headers=headers
        )
        job_id = job_response.json()["id"]
        
        # Verify job exists
        get_job = requests.get(
            f"{self.BASE_URL}/jobs/{job_id}",
            headers=headers
        )
        assert get_job.status_code == 200
        assert get_job.json()["id"] == job_id
        
        # Update job
        update_response = requests.put(
            f"{self.BASE_URL}/jobs/{job_id}",
            json={"title": "Updated Job"},
            headers=headers
        )
        assert update_response.status_code == 200
        
        # Verify update
        updated_job = requests.get(
            f"{self.BASE_URL}/jobs/{job_id}",
            headers=headers
        )
        assert updated_job.json()["title"] == "Updated Job"
        
        print("✅ Data consistency verified")
    
    def test_concurrent_operations(self, headers):
        """Test concurrent operations"""
        import concurrent.futures
        
        def create_job(i):
            response = requests.post(
                f"{self.BASE_URL}/jobs",
                json={
                    "title": f"Concurrent Job {i}",
                    "description": "Test",
                    "status": "active"
                },
                headers=headers
            )
            return response.status_code == 200
        
        # Create 10 jobs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(create_job, range(10)))
        
        assert all(results)
        print("✅ Concurrent operations handled correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

