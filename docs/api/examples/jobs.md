# Job Management Examples

## Create a Job

### Request

```bash
curl -X POST "https://api.resumescreening.com/api/v1/jobs" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Software Engineer",
    "description": "We are looking for an experienced software engineer...",
    "requirements_json": {
      "required_skills": ["Python", "FastAPI", "PostgreSQL"],
      "preferred_skills": ["Docker", "Kubernetes"],
      "min_experience_years": 5,
      "required_degree": "Bachelor's"
    },
    "status": "active"
  }'
```

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Senior Software Engineer",
  "description": "We are looking for an experienced software engineer...",
  "requirements_json": {
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "preferred_skills": ["Docker", "Kubernetes"],
    "min_experience_years": 5,
    "required_degree": "Bachelor's"
  },
  "status": "active",
  "created_by": "user-id",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

## List Jobs

### Request

```bash
curl -X GET "https://api.resumescreening.com/api/v1/jobs?page=1&page_size=10&status=active" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Senior Software Engineer",
      "status": "active",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

## Get Job Details

### Request

```bash
curl -X GET "https://api.resumescreening.com/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Update Job

### Request

```bash
curl -X PUT "https://api.resumescreening.com/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Job Title",
    "status": "closed"
  }'
```

## Delete Job

### Request

```bash
curl -X DELETE "https://api.resumescreening.com/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Response

**Status:** 200 OK

```json
{
  "message": "Job deleted successfully"
}
```

## Python Example

```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}

# Create job
job_data = {
    "title": "Senior Software Engineer",
    "description": "We are looking for...",
    "requirements_json": {
        "required_skills": ["Python", "FastAPI"],
        "min_experience_years": 5
    },
    "status": "active"
}

response = requests.post(
    "https://api.resumescreening.com/api/v1/jobs",
    json=job_data,
    headers=headers
)
job = response.json()
print(f"Created job: {job['id']}")

# List jobs
jobs = requests.get(
    "https://api.resumescreening.com/api/v1/jobs",
    headers=headers
).json()
print(f"Total jobs: {jobs['total']}")
```

