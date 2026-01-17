"""
Tests for database models
"""
import pytest
from datetime import datetime
from app.models.user import User
from app.models.job import Job
from app.models.resume import Resume
from app.models.candidate import Candidate
from app.models.match_result import MatchResult
from app.core.security import get_password_hash, verify_password


class TestUserModel:
    """Tests for User model"""
    
    def test_create_user(self, db_session):
        """Test creating a user"""
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.created_at is not None
    
    def test_user_password_verification(self, db_session):
        """Test password verification"""
        password = "testpassword123"
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash(password),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        assert verify_password(password, user.hashed_password) is True
        assert verify_password("wrongpassword", user.hashed_password) is False
    
    def test_user_unique_email(self, db_session):
        """Test that email must be unique"""
        user1 = User(
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            email="test@example.com",
            hashed_password=get_password_hash("password456"),
            is_active=True
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


class TestJobModel:
    """Tests for Job model"""
    
    def test_create_job(self, db_session, test_user):
        """Test creating a job"""
        job = Job(
            title="Software Engineer",
            description="Test job description",
            requirements_json={"skills": ["Python"]},
            status="active",
            created_by=test_user.id
        )
        db_session.add(job)
        db_session.commit()
        
        assert job.id is not None
        assert job.title == "Software Engineer"
        assert job.status == "active"
        assert job.created_at is not None
    
    def test_job_requirements_json(self, db_session, test_user):
        """Test job requirements JSON storage"""
        requirements = {
            "required_skills": ["Python", "FastAPI"],
            "min_experience_years": 3
        }
        job = Job(
            title="Test Job",
            description="Test",
            requirements_json=requirements,
            status="draft",
            created_by=test_user.id
        )
        db_session.add(job)
        db_session.commit()
        
        assert job.requirements_json == requirements
        assert job.requirements_json["required_skills"] == ["Python", "FastAPI"]


class TestResumeModel:
    """Tests for Resume model"""
    
    def test_create_resume(self, db_session, test_user):
        """Test creating a resume"""
        resume = Resume(
            file_path="/uploads/test.pdf",
            file_name="test.pdf",
            file_type="application/pdf",
            status="uploaded",
            uploaded_by=test_user.id
        )
        db_session.add(resume)
        db_session.commit()
        
        assert resume.id is not None
        assert resume.file_name == "test.pdf"
        assert resume.status == "uploaded"
    
    def test_resume_parsed_data(self, db_session, test_user):
        """Test resume parsed data JSON storage"""
        parsed_data = {
            "skills": ["Python", "JavaScript"],
            "experience": [{"title": "Engineer", "years": 5}]
        }
        resume = Resume(
            file_path="/uploads/test.pdf",
            file_name="test.pdf",
            file_type="application/pdf",
            parsed_data_json=parsed_data,
            status="parsed",
            uploaded_by=test_user.id
        )
        db_session.add(resume)
        db_session.commit()
        
        assert resume.parsed_data_json == parsed_data


class TestCandidateModel:
    """Tests for Candidate model"""
    
    def test_create_candidate(self, db_session, test_resume):
        """Test creating a candidate"""
        candidate = Candidate(
            anonymized_id="anon_123",
            resume_id=test_resume.id,
            masked_data_json={"name": "[MASKED]"}
        )
        db_session.add(candidate)
        db_session.commit()
        
        assert candidate.id is not None
        assert candidate.anonymized_id == "anon_123"
        assert candidate.resume_id == test_resume.id


class TestMatchResultModel:
    """Tests for MatchResult model"""
    
    def test_create_match_result(self, db_session, test_job, test_candidate):
        """Test creating a match result"""
        match_result = MatchResult(
            job_id=test_job.id,
            candidate_id=test_candidate.id,
            scores_json={
                "skills": 0.8,
                "experience": 0.9,
                "education": 0.7
            },
            rank=1,
            explanation="Good match"
        )
        db_session.add(match_result)
        db_session.commit()
        
        assert match_result.id is not None
        assert match_result.rank == 1
        assert match_result.scores_json["skills"] == 0.8

