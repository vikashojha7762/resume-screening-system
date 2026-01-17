# Testing Guide

Comprehensive guide to testing the Resume Screening System.

## Overview

This guide covers all aspects of testing, from unit tests to end-to-end testing.

## Test Types

### Unit Tests

Test individual components in isolation.

**Location:** `backend/tests/test_*.py`

**Run:**
```bash
pytest tests/test_models.py
pytest tests/test_services.py
```

### Integration Tests

Test component interactions.

**Location:** `backend/tests/test_integration.py`

**Run:**
```bash
pytest tests/test_integration.py -m integration
```

### API Tests

Test API endpoints.

**Location:** `backend/tests/test_api_endpoints.py`

**Run:**
```bash
pytest tests/test_api_endpoints.py
```

### E2E Tests

Test complete user workflows.

**Location:** `cypress/e2e/`

**Run:**
```bash
npx cypress open
```

## Writing Tests

### Test Structure

```python
def test_feature_name():
    """Test description"""
    # Arrange
    setup_data = create_test_data()
    
    # Act
    result = function_under_test(setup_data)
    
    # Assert
    assert result == expected_value
```

### Using Fixtures

```python
def test_with_fixture(test_user, test_job):
    """Test using fixtures"""
    # Use provided fixtures
    assert test_user.email == "test@example.com"
    assert test_job.title == "Software Engineer"
```

### Mocking External Services

```python
@patch('app.services.external_service.call')
def test_with_mock(mock_call):
    """Test with mocked external service"""
    mock_call.return_value = {"status": "success"}
    result = function_using_external_service()
    assert result["status"] == "success"
```

## Test Coverage

### Coverage Goals

- **Overall:** > 80%
- **Critical Paths:** > 90%
- **New Code:** > 80%

### Generating Coverage Reports

```bash
# Backend
pytest --cov=app --cov-report=html

# Frontend
npm test -- --coverage
```

## Performance Testing

### Load Testing with Locust

```bash
cd backend/tests/performance
locust -f locustfile.py --host=http://localhost:8000
```

### Benchmarking

```bash
pytest tests/performance/test_performance.py -m performance
```

## See Also

- [Test README](../../backend/tests/README.md)
- [Testing Best Practices](./testing-best-practices.md)

