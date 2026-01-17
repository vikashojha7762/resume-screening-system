"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.core.config import settings
import os

# Use test database
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_resume_screening")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def auth_headers(client, test_user_data):
    """Get authentication headers"""
    # Register user
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Login
    response = client.post("/api/v1/auth/login/json", json=test_user_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

