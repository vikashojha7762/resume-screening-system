"""
Mock fixtures for external services
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import boto3
from moto import mock_s3


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.exists.return_value = False
    mock_redis.ping.return_value = True
    return mock_redis


@pytest.fixture
def mock_s3_client():
    """Mock S3 client using moto"""
    with mock_s3():
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        yield s3_client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_celery_task():
    """Mock Celery task"""
    with patch('app.celery_app.celery.send_task') as mock_task:
        mock_task.return_value = MagicMock(id='test-task-id')
        yield mock_task


@pytest.fixture
def mock_file_upload():
    """Mock file upload"""
    mock_file = MagicMock()
    mock_file.filename = "test_resume.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.size = 1024
    mock_file.read.return_value = b"PDF content"
    return mock_file


@pytest.fixture
def mock_email_service():
    """Mock email service"""
    with patch('app.services.email_service.send_email') as mock_send:
        mock_send.return_value = True
        yield mock_send

