"""
Database fixtures for testing
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models.user import User
from app.models.job import Job
from app.models.resume import Resume
from app.models.candidate import Candidate
from app.models.match_result import MatchResult
from app.core.security import get_password_hash


@pytest.fixture(scope="function")
def test_db():
    """Create a test database in memory"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Provide a database session"""
    return test_db


@pytest.fixture(scope="function")
def override_get_db(test_db):
    """Override get_db dependency"""
    def _get_db():
        try:
            yield test_db
        finally:
            pass
    return _get_db


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_superuser(db_session):
    """Create a test superuser"""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_job(db_session, test_user):
    """Create a test job"""
    job = Job(
        title="Software Engineer",
        description="We are looking for a skilled software engineer",
        requirements_json={
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
            "min_experience_years": 3,
            "required_degree": "Bachelor's"
        },
        status="active",
        created_by=test_user.id
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def test_resume(db_session, test_user):
    """Create a test resume"""
    resume = Resume(
        file_path="/uploads/test_resume.pdf",
        file_name="test_resume.pdf",
        file_type="application/pdf",
        status="processed",
        parsed_data_json={
            "skills": ["Python", "FastAPI"],
            "experience": [{"title": "Software Engineer", "years": 5}],
            "education": [{"degree": "Bachelor's", "field": "Computer Science"}]
        },
        uploaded_by=test_user.id
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    return resume


@pytest.fixture
def test_candidate(db_session, test_resume):
    """Create a test candidate"""
    candidate = Candidate(
        anonymized_id="anon_123",
        resume_id=test_resume.id,
        masked_data_json={"name": "[MASKED]", "email": "[MASKED]"}
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    return candidate

