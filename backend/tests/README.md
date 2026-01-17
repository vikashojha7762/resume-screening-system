# Testing Suite Documentation

## Overview

This directory contains comprehensive tests for the Resume Screening System.

## Test Structure

```
tests/
├── fixtures/          # Test fixtures and mocks
├── performance/       # Performance and load tests
├── factories.py       # Test data factories
├── test_models.py     # Database model tests
├── test_services.py   # Service layer tests
├── test_api_endpoints.py  # API endpoint tests
├── test_nlp_accuracy.py   # NLP accuracy tests
├── test_integration.py    # Integration tests
├── test_security.py       # Security tests
└── test_data_generators.py # Test data generators
```

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test Suite
```bash
pytest tests/test_models.py
pytest tests/test_api_endpoints.py
pytest tests/test_security.py
```

### With Coverage
```bash
pytest --cov=app --cov-report=html
```

### Performance Tests
```bash
pytest tests/performance/ -m performance
```

### Security Tests
```bash
pytest tests/test_security.py -m security
```

## Test Categories

### Unit Tests
- Model tests
- Service tests
- Utility function tests

### Integration Tests
- End-to-end workflows
- Database integration
- External service integration

### Performance Tests
- API response times
- Database query performance
- Load testing with Locust

### Security Tests
- Authentication/authorization
- SQL injection prevention
- XSS prevention
- File upload security

## Test Data

Test data is generated using factories and Faker. See `factories.py` for available factories.

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Commits to main/develop branches
- Manual triggers

## Coverage Goals

- Overall: > 80%
- Critical paths: > 90%
- Security: 100%

