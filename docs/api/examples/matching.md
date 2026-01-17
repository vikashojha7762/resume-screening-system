# Matching Examples

## Match Job to Candidates

### Request

```bash
curl -X POST "https://api.resumescreening.com/api/v1/results/job/550e8400-e29b-41d4-a716-446655440000/match" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "standard",
    "diversity_weight": 0.1,
    "enable_bias_detection": true
  }'
```

### Response

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_title": "Senior Software Engineer",
  "candidates_matched": 50,
  "ranked_results": [
    {
      "candidate_id": "candidate-1",
      "anonymized_id": "anon_123",
      "rank": 1,
      "overall_score": 0.95,
      "component_scores": {
        "skills": 0.90,
        "experience": 0.95,
        "education": 0.85
      },
      "explanation": "Excellent match with all required skills...",
      "ranking_explanation": "Ranked #1 due to high overall score..."
    }
  ],
  "bias_detection": {
    "overall_bias_score": 0.2,
    "recommendations": [
      "Consider broadening skill requirements",
      "Review for age-related language"
    ]
  },
  "processing_time_seconds": 3.5,
  "strategy_used": "standard"
}
```

## Get Ranked Results

### Request

```bash
curl -X GET "https://api.resumescreening.com/api/v1/results/job/550e8400-e29b-41d4-a716-446655440000/ranked?limit=100&min_score=0.7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Response

```json
{
  "items": [
    {
      "id": "result-1",
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "candidate_id": "candidate-1",
      "rank": 1,
      "overall_score": 0.95,
      "scores_json": {
        "skills": 0.90,
        "experience": 0.95,
        "education": 0.85
      },
      "explanation": "Excellent match...",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 100
}
```

## Matching Strategies

### Standard Strategy

```json
{
  "strategy": "standard"
}
```

Full scoring with all components (skills, experience, education).

### Fast Strategy

```json
{
  "strategy": "fast"
}
```

Uses FAISS for vector similarity search - faster for large candidate pools.

### Comprehensive Strategy

```json
{
  "strategy": "comprehensive"
}
```

Standard + additional analysis and bias detection.

## Python Example

```python
import requests
import time

headers = {"Authorization": "Bearer YOUR_TOKEN"}
job_id = "550e8400-e29b-41d4-a716-446655440000"

# Start matching
match_response = requests.post(
    f"https://api.resumescreening.com/api/v1/results/job/{job_id}/match",
    json={
        "strategy": "standard",
        "diversity_weight": 0.1,
        "enable_bias_detection": True
    },
    headers=headers
)
match_result = match_response.json()

print(f"Matched {match_result['candidates_matched']} candidates")
print(f"Processing time: {match_result['processing_time_seconds']}s")

# Get top candidates
for candidate in match_result['ranked_results'][:10]:
    print(f"Rank {candidate['rank']}: Score {candidate['overall_score']:.2f}")
```

## JavaScript Example

```javascript
// Match candidates
const matchResponse = await fetch(
  `https://api.resumescreening.com/api/v1/results/job/${jobId}/match`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      strategy: 'standard',
      diversity_weight: 0.1,
      enable_bias_detection: true
    })
  }
);

const matchResult = await matchResponse.json();
console.log(`Matched ${matchResult.candidates_matched} candidates`);

// Display top candidates
matchResult.ranked_results.slice(0, 10).forEach(candidate => {
  console.log(`Rank ${candidate.rank}: ${candidate.overall_score}`);
});
```

## Score Breakdown

Each candidate receives scores in three categories:

- **Skills Score (50% weight):** Match between job requirements and candidate skills
- **Experience Score (30% weight):** Years of experience and relevance
- **Education Score (20% weight):** Degree match and institution tier

## Bias Detection

The API can detect and report potential biases:

- **Gender bias:** Masculine/feminine language in job descriptions
- **Age bias:** Age-related language patterns
- **Institution bias:** Elite institution preferences

Enable with `enable_bias_detection: true` in the match request.

