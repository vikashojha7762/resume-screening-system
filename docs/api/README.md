# API Documentation

Complete API reference for the Resume Screening System.

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
- [Interactive Documentation](#interactive-documentation)

## Overview

The Resume Screening System API is a RESTful API built with FastAPI. All endpoints return JSON responses and use standard HTTP status codes.

### API Version

Current version: **v1**  
Base path: `/api/v1`

## Base URL

**Production:** `https://api.resumescreening.com/api/v1`  
**Staging:** `https://staging-api.resumescreening.com/api/v1`  
**Development:** `http://localhost:8000/api/v1`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

### Getting an Access Token

**Endpoint:** `POST /auth/login/json`

**Request:**
```json
{
  "username": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Token Expiration

- Access tokens expire after **30 minutes**
- Refresh tokens expire after **7 days**

## Rate Limiting

API requests are rate-limited to ensure fair usage:

- **Authenticated users:** 100 requests per minute
- **Unauthenticated users:** 10 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### Common Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `AUTH_REQUIRED` | Authentication required | Include valid JWT token |
| `AUTH_EXPIRED` | Token expired | Request new token |
| `VALIDATION_ERROR` | Invalid request data | Check request format |
| `NOT_FOUND` | Resource not found | Verify resource ID |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait before retrying |

## Endpoints

### Authentication

#### Register User
```
POST /auth/register
```

#### Login
```
POST /auth/login/json
```

#### Get Current User
```
GET /auth/me
```

### Jobs

#### List Jobs
```
GET /jobs?page=1&page_size=10&status=active
```

#### Get Job
```
GET /jobs/{job_id}
```

#### Create Job
```
POST /jobs
```

#### Update Job
```
PUT /jobs/{job_id}
```

#### Delete Job
```
DELETE /jobs/{job_id}
```

### Resumes

#### Upload Resume
```
POST /resumes/upload
Content-Type: multipart/form-data
```

#### List Resumes
```
GET /resumes?page=1&page_size=10&status=processed
```

#### Get Resume
```
GET /resumes/{resume_id}
```

#### Delete Resume
```
DELETE /resumes/{resume_id}
```

### Results

#### Get Ranked Results
```
GET /results/job/{job_id}/ranked?limit=100&min_score=0.5
```

#### Match Job to Candidates
```
POST /results/job/{job_id}/match
```

## Interactive Documentation

### Swagger UI

Access interactive API documentation at:
- **Development:** `http://localhost:8000/docs`
- **Production:** `https://api.resumescreening.com/docs`

### ReDoc

Alternative documentation format:
- **Development:** `http://localhost:8000/redoc`
- **Production:** `https://api.resumescreening.com/redoc`

### OpenAPI Specification

Download the OpenAPI spec:
- **JSON:** `/openapi.json`
- **YAML:** `/openapi.yaml`

## Request/Response Examples

See detailed examples in:
- [Authentication Examples](./examples/authentication.md)
- [Job Management Examples](./examples/jobs.md)
- [Resume Upload Examples](./examples/resumes.md)
- [Matching Examples](./examples/matching.md)

## SDKs and Libraries

Official SDKs coming soon. For now, use standard HTTP clients:

- **Python:** `requests`, `httpx`
- **JavaScript:** `axios`, `fetch`
- **cURL:** See examples in each endpoint section

## Support

For API support:
- **Email:** api-support@resumescreening.com
- **Documentation Issues:** Open an issue on GitHub
- **Emergency:** See support escalation matrix

