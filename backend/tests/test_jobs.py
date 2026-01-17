"""
Tests for job endpoints
"""
import pytest
from fastapi import status


def test_create_job(client, auth_headers):
    """Test creating a job"""
    job_data = {
        "title": "Software Engineer",
        "description": "We are looking for a software engineer",
        "requirements_json": {
            "skills": ["Python", "FastAPI"],
            "experience": "2+ years"
        }
    }
    
    response = client.post("/api/v1/jobs", json=job_data, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == job_data["title"]
    assert "id" in data


def test_list_jobs(client, auth_headers):
    """Test listing jobs"""
    # Create a job first
    job_data = {
        "title": "Software Engineer",
        "description": "Test description"
    }
    client.post("/api/v1/jobs", json=job_data, headers=auth_headers)
    
    # List jobs
    response = client.get("/api/v1/jobs", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) > 0


def test_get_job(client, auth_headers):
    """Test getting a specific job"""
    # Create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test description"
    }
    create_response = client.post("/api/v1/jobs", json=job_data, headers=auth_headers)
    job_id = create_response.json()["id"]
    
    # Get the job
    response = client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == job_id
    assert data["title"] == job_data["title"]


def test_update_job(client, auth_headers):
    """Test updating a job"""
    # Create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test description"
    }
    create_response = client.post("/api/v1/jobs", json=job_data, headers=auth_headers)
    job_id = create_response.json()["id"]
    
    # Update the job
    update_data = {
        "title": "Senior Software Engineer",
        "description": "Updated description"
    }
    response = client.put(f"/api/v1/jobs/{job_id}", json=update_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == update_data["title"]


def test_delete_job(client, auth_headers):
    """Test deleting a job"""
    # Create a job
    job_data = {
        "title": "Software Engineer",
        "description": "Test description"
    }
    create_response = client.post("/api/v1/jobs", json=job_data, headers=auth_headers)
    job_id = create_response.json()["id"]
    
    # Delete the job
    response = client.delete(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify it's deleted
    get_response = client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

