# Developer Documentation

Welcome developers! This guide will help you set up your development environment and contribute to the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Contributing Guidelines](#contributing-guidelines)
- [Code Style Guide](#code-style-guide)
- [Testing Guide](#testing-guide)
- [API Development](#api-development)
- [Deployment Guide](#deployment-guide)

## Development Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+** (with pgvector)
- **Redis 7+**
- **Docker & Docker Compose** (recommended)
- **Git**

### Quick Start

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourorg/resume-screening.git
   cd resume-screening
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database Setup**
   ```bash
   # Using Docker Compose
   docker-compose up -d postgres redis
   
   # Run migrations
   cd backend
   alembic upgrade head
   ```

6. **Run Development Servers**
   ```bash
   # Backend (Terminal 1)
   cd backend
   uvicorn app.main:app --reload
   
   # Frontend (Terminal 2)
   cd frontend
   npm run dev
   ```

### Docker Development

```bash
# Start all services
docker-compose up

# Start specific services
docker-compose up backend frontend

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## Project Structure

```
resume-screening/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core utilities
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── tasks/        # Celery tasks
│   ├── alembic/          # Database migrations
│   ├── tests/            # Test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── store/        # Redux store
│   │   └── services/      # API services
│   └── package.json
├── docs/                 # Documentation
├── k8s/                  # Kubernetes manifests
└── docker-compose.yml
```

## Contributing Guidelines

### Workflow

1. **Fork Repository**
2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make Changes**
4. **Write Tests**
5. **Run Tests**
   ```bash
   pytest
   npm test
   ```
6. **Commit Changes**
   ```bash
   git commit -m "Add feature: description"
   ```
7. **Push to Branch**
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Create Pull Request**

### Commit Messages

Follow conventional commits:

```
feat: Add resume upload progress tracking
fix: Resolve matching score calculation bug
docs: Update API documentation
test: Add integration tests for matching
refactor: Simplify resume parser logic
```

### Pull Request Checklist

- [ ] Code follows style guide
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No linter errors
- [ ] Commit messages follow convention

## Code Style Guide

### Python (Backend)

Follow PEP 8 with these additions:

- **Line Length:** 100 characters
- **Imports:** Sorted with isort
- **Type Hints:** Required for all functions
- **Docstrings:** Google style

**Example:**
```python
def calculate_match_score(
    job_requirements: Dict[str, Any],
    candidate_data: Dict[str, Any]
) -> float:
    """
    Calculate match score between job and candidate.
    
    Args:
        job_requirements: Job requirements dictionary
        candidate_data: Candidate data dictionary
        
    Returns:
        Match score between 0.0 and 1.0
    """
    # Implementation
    pass
```

**Linting:**
```bash
# Format code
black app/
isort app/

# Lint
flake8 app/
mypy app/
```

### TypeScript (Frontend)

- **Style:** ESLint + Prettier
- **Type Safety:** Strict mode enabled
- **Components:** Functional components with hooks
- **Naming:** PascalCase for components, camelCase for functions

**Example:**
```typescript
interface JobCardProps {
  job: Job;
  onSelect: (jobId: string) => void;
}

const JobCard: React.FC<JobCardProps> = ({ job, onSelect }) => {
  return (
    <Card onClick={() => onSelect(job.id)}>
      <Typography variant="h6">{job.title}</Typography>
    </Card>
  );
};
```

**Linting:**
```bash
npm run lint
npm run format
```

## Testing Guide

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run with markers
pytest -m unit
pytest -m integration
```

### Frontend Tests

```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

### E2E Tests

```bash
# Start application
docker-compose up

# Run Cypress
cd frontend
npx cypress open
```

## API Development

### Adding New Endpoints

1. **Create Schema** (`app/schemas/`)
   ```python
   class NewResourceCreate(BaseModel):
       name: str
       description: Optional[str] = None
   ```

2. **Create Model** (`app/models/`)
   ```python
   class NewResource(Base):
       __tablename__ = "new_resources"
       id = Column(UUID, primary_key=True)
       name = Column(String, nullable=False)
   ```

3. **Create Endpoint** (`app/api/v1/`)
   ```python
   @router.post("/new-resources")
   async def create_resource(
       resource: NewResourceCreate,
       db: Session = Depends(get_db)
   ):
       # Implementation
       pass
   ```

4. **Add Tests** (`tests/test_api_endpoints.py`)

5. **Update Documentation**

### API Versioning

- Current version: `v1`
- New versions: Create new router in `app/api/v2/`
- Deprecation: Mark old endpoints, remove after 6 months

## Deployment Guide

See [Operations Documentation](../operations/deployment.md) for detailed deployment instructions.

### Quick Deploy

```bash
# Build images
docker-compose build

# Deploy to staging
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n resume-screening
```

## Development Tools

### Recommended IDE Setup

**VS Code Extensions:**
- Python
- Pylance
- ESLint
- Prettier
- Docker

**PyCharm:**
- Python plugin
- Docker integration
- Database tools

### Useful Commands

```bash
# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Format code
black app/
isort app/
npm run format

# Type checking
mypy app/
npm run type-check

# Run development server
uvicorn app.main:app --reload
npm run dev
```

## Getting Help

- **Documentation:** See docs/ directory
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Email:** dev-team@resumescreening.com

## See Also

- [API Documentation](../api/README.md)
- [Testing Documentation](../../backend/tests/README.md)
- [Architecture Documentation](../architecture/README.md)

