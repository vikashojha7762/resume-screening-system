# Candidate-to-Job Matching Implementation

## Overview
Implemented a comprehensive candidate-to-job matching system with weighted scoring (Skills: 50%, Experience: 30%, Semantic Similarity: 20%).

## Implementation Details

### 1. Backend Service: `candidate_matcher.py`
**Location**: `backend/app/services/candidate_matcher.py`

**Key Features**:
- **Weighted Scoring**:
  - Skills Match: 50% weight
  - Experience Match: 30% weight
  - Semantic Similarity: 20% weight
- **Skill Matching**:
  - Extracts required and preferred skills from job requirements
  - Matches against resume skills (case-insensitive)
  - Calculates match percentage (required skills weighted 70%, preferred 30%)
  - Returns matched and missing skills
- **Experience Matching**:
  - Extracts total years from resume experience data
  - Compares against job required/preferred experience years
  - Provides detailed experience summary
- **Semantic Similarity**:
  - Generates BERT embeddings for job description
  - Uses existing resume embeddings or generates on-the-fly
  - Calculates cosine similarity between embeddings
  - Normalizes to 0-1 range

### 2. API Endpoint
**Endpoint**: `POST /api/v1/jobs/{job_id}/match-candidates`

**Location**: `backend/app/api/v1/jobs.py`

**Request**:
```http
POST /api/v1/jobs/{job_id}/match-candidates
Authorization: Bearer <token>
```

**Response**:
```json
{
  "job_id": "uuid",
  "job_title": "Software Engineer",
  "candidates_matched": 5,
  "matching_weights": {
    "skills": 0.5,
    "experience": 0.3,
    "semantic": 0.2
  },
  "ranked_candidates": [
    {
      "candidate_id": "uuid",
      "anonymized_id": "CAN-001",
      "resume_id": "uuid",
      "resume_file_name": "john_doe_resume.pdf",
      "candidate_name": "John Doe",
      "final_score": 85.5,
      "rank": 1,
      "component_scores": {
        "skills": 90.0,
        "experience": 80.0,
        "semantic_similarity": 75.0
      },
      "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
      "missing_skills": ["Docker", "Kubernetes"],
      "experience_summary": "Meets experience requirement (5.0 years)"
    }
  ]
}
```

### 3. Frontend Integration

**Updated Files**:
- `frontend/src/store/slices/candidatesSlice.ts`: Updated to use new endpoint
- `frontend/src/pages/Candidates.tsx`: Enhanced UI to display match details
- `frontend/src/types/index.ts`: Extended MatchResult interface

**Features**:
- "Match Candidates" button triggers the matching API
- Displays ranked candidates with:
  - Final match score
  - Component scores (Skills, Experience, Semantic)
  - Matched and missing skills
  - Experience summary
  - Candidate name and resume file name

## Usage Flow

1. **Upload Resumes**: Resumes are uploaded and processed (parsed, skills extracted, embeddings generated)
2. **Create Job**: Create a job posting with:
   - Title and description
   - Required/preferred skills in `requirements_json`
   - Required/preferred experience years
3. **Match Candidates**: Click "Match Candidates" button in Candidates section
4. **View Results**: See ranked list of candidates with detailed match scores

## Example API Request/Response

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/{job_id}/match-candidates" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

### Response Example
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "job_title": "Senior Python Developer",
  "candidates_matched": 3,
  "matching_weights": {
    "skills": 0.5,
    "experience": 0.3,
    "semantic": 0.2
  },
  "ranked_candidates": [
    {
      "candidate_id": "456e7890-e89b-12d3-a456-426614174001",
      "anonymized_id": "CAN-001",
      "resume_id": "789e0123-e89b-12d3-a456-426614174002",
      "resume_file_name": "john_doe.pdf",
      "candidate_name": "John Doe",
      "final_score": 87.5,
      "rank": 1,
      "component_scores": {
        "skills": 95.0,
        "experience": 85.0,
        "semantic_similarity": 70.0
      },
      "matched_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
      "missing_skills": ["Kubernetes"],
      "experience_summary": "Exceeds preferred experience (8.5 years)"
    }
  ]
}
```

## Technical Details

### Skill Matching Algorithm
1. Normalize all skills to lowercase
2. Extract required and preferred skills from job requirements
3. Match against resume skills
4. Calculate score: `(required_matched/required_total * 0.7) + (preferred_matched/preferred_total * 0.3)`

### Experience Matching Algorithm
1. Extract total years from resume experience data
2. Compare against job requirements:
   - If meets/exceeds required: score = 1.0
   - If between required and preferred: linear interpolation
   - If below required: proportional score (years/required)

### Semantic Similarity Algorithm
1. Generate BERT embedding for job description (title + description)
2. Retrieve or generate embedding for resume
3. Calculate cosine similarity
4. Normalize to 0-1 range: `(similarity + 1) / 2`

### Final Score Calculation
```python
final_score = (
    skill_score * 0.50 +
    experience_score * 0.30 +
    semantic_score * 0.20
) * 100  # Convert to percentage
```

## Error Handling

- **Job Not Found**: Returns 404 with error message
- **No Processed Candidates**: Returns empty list with informative message
- **Missing Resume Data**: Skips candidate and logs warning
- **Embedding Generation Failure**: Falls back to 0.0 for semantic score
- **Database Errors**: Logs error and returns 500 with error details

## Testing

To test the implementation:

1. **Start Backend**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test Flow**:
   - Upload resumes (ensure they are processed)
   - Create a job with skills and experience requirements
   - Navigate to Candidates section
   - Select the job
   - Click "Match Candidates"
   - Verify ranked results appear

## Notes

- The matching service only processes candidates with `status = 'processed'`
- Job embeddings are generated on-the-fly (not cached)
- Resume embeddings are reused if available, otherwise generated from raw text
- All scores are normalized to 0-100 percentage range for display

