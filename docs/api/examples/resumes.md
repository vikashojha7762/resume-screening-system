# Resume Upload Examples

## Upload Resume

### Request

```bash
curl -X POST "https://api.resumescreening.com/api/v1/resumes/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/resume.pdf"
```

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "resume.pdf",
  "file_type": "application/pdf",
  "file_size": 245678,
  "status": "uploaded",
  "message": "Resume uploaded successfully. Processing started.",
  "created_at": "2024-01-01T12:00:00Z"
}
```

## List Resumes

### Request

```bash
curl -X GET "https://api.resumescreening.com/api/v1/resumes?page=1&page_size=10&status=processed" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "file_name": "resume.pdf",
      "status": "processed",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

## Get Resume Details

### Request

```bash
curl -X GET "https://api.resumescreening.com/api/v1/resumes/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "resume.pdf",
  "file_type": "application/pdf",
  "status": "processed",
  "parsed_data_json": {
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "experience": [
      {
        "title": "Software Engineer",
        "company": "Tech Corp",
        "duration_months": 24
      }
    ],
    "education": [
      {
        "degree": "Bachelor's",
        "institution": "University",
        "field": "Computer Science"
      }
    ]
  },
  "created_at": "2024-01-01T12:00:00Z"
}
```

## Python Example

```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}

# Upload resume
with open("resume.pdf", "rb") as f:
    files = {"file": ("resume.pdf", f, "application/pdf")}
    response = requests.post(
        "https://api.resumescreening.com/api/v1/resumes/upload",
        files=files,
        headers=headers
    )
    resume = response.json()
    print(f"Uploaded: {resume['id']}")

# Check processing status
resume_id = resume['id']
status_response = requests.get(
    f"https://api.resumescreening.com/api/v1/resumes/{resume_id}",
    headers=headers
)
status = status_response.json()["status"]
print(f"Status: {status}")
```

## JavaScript Example

```javascript
// Upload resume
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('https://api.resumescreening.com/api/v1/resumes/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const resume = await response.json();
console.log('Uploaded:', resume.id);
```

## Supported File Formats

- PDF (`.pdf`)
- Microsoft Word (`.doc`, `.docx`)
- Plain Text (`.txt`)

## File Size Limits

- Maximum file size: **10 MB**
- Recommended: Under 5 MB for faster processing

## Processing Status

Resumes go through these statuses:

1. `uploaded` - File uploaded successfully
2. `parsing` - Extracting text from file
3. `parsed` - Text extracted, analyzing content
4. `processing` - Running NLP analysis
5. `processed` - Analysis complete
6. `error` - Processing failed

## Error Responses

### File Too Large

**Status:** 400 Bad Request

```json
{
  "detail": "File size exceeds maximum limit of 10MB",
  "error_code": "FILE_TOO_LARGE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Invalid File Type

**Status:** 400 Bad Request

```json
{
  "detail": "Invalid file type. Supported: pdf, doc, docx, txt",
  "error_code": "INVALID_FILE_TYPE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

