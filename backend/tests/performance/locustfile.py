"""
Load testing with Locust
"""
from locust import HttpUser, task, between
import random


class ResumeScreeningUser(HttpUser):
    """Simulated user for load testing"""
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tasks"""
        response = self.client.post(
            "/api/v1/auth/login/json",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def view_jobs(self):
        """View jobs list"""
        self.client.get("/api/v1/jobs", headers=self.headers)
    
    @task(2)
    def view_resumes(self):
        """View resumes list"""
        self.client.get("/api/v1/resumes", headers=self.headers)
    
    @task(1)
    def upload_resume(self):
        """Upload a resume"""
        file_content = b"PDF content for testing"
        self.client.post(
            "/api/v1/resumes/upload",
            files={"file": ("test.pdf", file_content, "application/pdf")},
            headers=self.headers
        )
    
    @task(2)
    def get_results(self):
        """Get match results"""
        job_id = random.randint(1, 100)
        self.client.get(
            f"/api/v1/results/job/{job_id}/ranked",
            headers=self.headers
        )
    
    @task(1)
    def match_candidates(self):
        """Match candidates to job"""
        job_id = random.randint(1, 100)
        self.client.post(
            f"/api/v1/results/job/{job_id}/match",
            json={"strategy": "standard"},
            headers=self.headers
        )


class HighLoadUser(HttpUser):
    """High load user for stress testing"""
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Quick login"""
        response = self.client.post(
            "/api/v1/auth/login/json",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        if response.status_code == 200:
            self.headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        else:
            self.headers = {}
    
    @task(10)
    def rapid_requests(self):
        """Make rapid requests"""
        self.client.get("/api/v1/jobs", headers=self.headers)

