# Database Schema Documentation

## Overview

The Resume Screening System uses PostgreSQL 14 with the pgvector extension for vector similarity search.

## Entity Relationship Diagram

```
┌─────────────┐
│    Users    │
│─────────────│
│ id (PK)     │
│ email       │
│ password    │
│ is_active   │
│ is_superuser│
└─────────────┘
      │
      │ 1
      │
      │ *
┌─────────────┐
│    Jobs     │
│─────────────│
│ id (PK)     │
│ title       │
│ description │
│ requirements│
│ status      │
│ created_by  │──┐
└─────────────┘  │
                 │
┌─────────────┐  │
│   Resumes   │  │
│─────────────│  │
│ id (PK)     │  │
│ file_path   │  │
│ parsed_data │  │
│ embedding   │  │
│ status      │  │
│ uploaded_by│──┘
└─────────────┘
      │
      │ 1
      │
      │ 1
┌─────────────┐
│  Candidates │
│─────────────│
│ id (PK)     │
│ anonymized  │
│ resume_id  │
│ masked_data │
└─────────────┘
      │
      │ 1
      │
      │ *
┌─────────────┐
│Match Results│
│─────────────│
│ id (PK)     │
│ job_id      │
│ candidate_id│
│ scores      │
│ rank        │
│ explanation │
└─────────────┘
```

## Tables

### users

Stores user accounts and authentication information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| is_active | BOOLEAN | DEFAULT true | Account active status |
| is_superuser | BOOLEAN | DEFAULT false | Admin privileges |
| created_at | TIMESTAMP | DEFAULT now() | Account creation time |
| updated_at | TIMESTAMP | DEFAULT now() | Last update time |

**Indexes:**
- `idx_users_email` on `email`

### jobs

Stores job postings and requirements.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique job identifier |
| title | VARCHAR(255) | NOT NULL | Job title |
| description | TEXT | NOT NULL | Job description |
| requirements_json | JSONB | | Job requirements |
| status | VARCHAR(50) | DEFAULT 'draft' | Job status |
| created_by | UUID | FOREIGN KEY → users.id | Creator user ID |
| created_at | TIMESTAMP | DEFAULT now() | Creation time |
| updated_at | TIMESTAMP | DEFAULT now() | Last update time |

**Indexes:**
- `idx_jobs_status` on `status`
- `idx_jobs_created_by` on `created_by`
- `idx_jobs_requirements` on `requirements_json` (GIN index)

### resumes

Stores uploaded resumes and parsed data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique resume identifier |
| file_path | VARCHAR(500) | NOT NULL | S3 file path |
| file_name | VARCHAR(255) | NOT NULL | Original filename |
| file_type | VARCHAR(100) | | MIME type |
| file_size | BIGINT | | File size in bytes |
| parsed_data_json | JSONB | | Extracted resume data |
| embedding_vector | vector(768) | | BERT embedding vector |
| status | VARCHAR(50) | DEFAULT 'uploaded' | Processing status |
| uploaded_by | UUID | FOREIGN KEY → users.id | Uploader user ID |
| created_at | TIMESTAMP | DEFAULT now() | Upload time |
| updated_at | TIMESTAMP | DEFAULT now() | Last update time |

**Indexes:**
- `idx_resumes_status` on `status`
- `idx_resumes_uploaded_by` on `uploaded_by`
- `idx_resumes_embedding` on `embedding_vector` (vector similarity)

### candidates

Stores anonymized candidate records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique candidate identifier |
| anonymized_id | VARCHAR(100) | UNIQUE | Anonymized identifier |
| resume_id | UUID | FOREIGN KEY → resumes.id | Associated resume |
| masked_data_json | JSONB | | Masked PII data |
| created_at | TIMESTAMP | DEFAULT now() | Creation time |
| updated_at | TIMESTAMP | DEFAULT now() | Last update time |

**Indexes:**
- `idx_candidates_anonymized_id` on `anonymized_id`
- `idx_candidates_resume_id` on `resume_id`

### match_results

Stores matching scores and rankings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique result identifier |
| job_id | UUID | FOREIGN KEY → jobs.id | Job identifier |
| candidate_id | UUID | FOREIGN KEY → candidates.id | Candidate identifier |
| scores_json | JSONB | NOT NULL | Component scores |
| overall_score | DECIMAL(5,2) | | Overall match score |
| rank | INTEGER | | Ranking position |
| explanation | TEXT | | Score explanation |
| created_at | TIMESTAMP | DEFAULT now() | Creation time |
| updated_at | TIMESTAMP | DEFAULT now() | Last update time |

**Indexes:**
- `idx_match_results_job_id` on `job_id`
- `idx_match_results_candidate_id` on `candidate_id`
- `idx_match_results_rank` on `(job_id, rank)`
- `idx_match_results_score` on `(job_id, overall_score DESC)`

### processing_queue

Tracks async processing tasks.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique task identifier |
| job_id | UUID | FOREIGN KEY → jobs.id | Associated job |
| resume_id | UUID | FOREIGN KEY → resumes.id | Associated resume |
| task_id | VARCHAR(255) | | Celery task ID |
| status | VARCHAR(50) | DEFAULT 'pending' | Task status |
| error_message | TEXT | | Error details if failed |
| created_at | TIMESTAMP | DEFAULT now() | Creation time |
| updated_at | TIMESTAMP | DEFAULT now() | Last update time |

**Indexes:**
- `idx_processing_queue_status` on `status`
- `idx_processing_queue_task_id` on `task_id`

## JSON Schema Examples

### requirements_json (jobs table)

```json
{
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "preferred_skills": ["Docker", "Kubernetes"],
  "min_experience_years": 5,
  "required_degree": "Bachelor's",
  "preferred_institutions": ["MIT", "Stanford"],
  "mandatory_requirements": {
    "skills": ["Python"],
    "min_experience_years": 3
  }
}
```

### parsed_data_json (resumes table)

```json
{
  "skills": [
    {"name": "Python", "category": "Programming", "confidence": 0.95},
    {"name": "FastAPI", "category": "Framework", "confidence": 0.90}
  ],
  "experience": [
    {
      "title": "Software Engineer",
      "company": "Tech Corp",
      "start_date": "2020-01-01",
      "end_date": "2023-12-31",
      "duration_months": 36
    }
  ],
  "education": [
    {
      "degree": "Bachelor's",
      "institution": "University",
      "field": "Computer Science",
      "graduation_year": 2020
    }
  ]
}
```

### scores_json (match_results table)

```json
{
  "skills": 0.90,
  "experience": 0.95,
  "education": 0.85,
  "breakdown": {
    "skills": {
      "score": 0.90,
      "matched_skills": ["Python", "FastAPI"],
      "missing_skills": []
    },
    "experience": {
      "score": 0.95,
      "total_years": 5.0,
      "required_years": 3
    }
  }
}
```

## Vector Search

The `embedding_vector` column uses pgvector for semantic similarity search:

```sql
-- Find similar resumes
SELECT id, file_name, 
       1 - (embedding_vector <=> query_vector) as similarity
FROM resumes
ORDER BY embedding_vector <=> query_vector
LIMIT 10;
```

## Migrations

Database schema is managed with Alembic. See migration files in `backend/alembic/versions/`.

## Backup and Recovery

- **Automated Backups:** Daily at 2 AM UTC
- **Retention:** 30 days local, 90 days S3
- **Point-in-Time Recovery:** Supported via WAL archiving

