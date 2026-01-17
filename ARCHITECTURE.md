# Architecture Documentation

## System Overview

The Resume Screening System is built with a microservices architecture using Docker Compose, featuring:

- **FastAPI Backend**: Python-based REST API
- **React Frontend**: TypeScript-based SPA
- **PostgreSQL 14 + pgvector**: Vector database for semantic search
- **Redis 7**: Caching and message broker
- **Celery**: Asynchronous task processing

## Service Architecture

### Backend Services

#### FastAPI Application (`backend`)
- **Port**: 8000
- **Hot Reload**: Enabled in development
- **Health Checks**: `/health`, `/health/live`, `/health/ready`
- **Features**:
  - RESTful API endpoints
  - JWT authentication
  - Database ORM (SQLAlchemy)
  - Redis caching
  - Celery task integration

#### Celery Worker (`celery-worker`)
- **Purpose**: Background task processing
- **Concurrency**: 4 workers (configurable)
- **Tasks**:
  - Resume processing
  - AI analysis
  - File uploads
  - Scheduled cleanup

#### Celery Beat (`celery-beat`)
- **Purpose**: Scheduled task execution
- **Schedule**:
  - Process pending resumes: Every 5 minutes
  - Cleanup old results: Every hour

### Data Services

#### PostgreSQL 14 with pgvector
- **Port**: 5432
- **Extensions**: `vector` (pgvector)
- **Purpose**:
  - Primary database
  - Vector embeddings storage
  - Semantic similarity search

#### Redis 7
- **Port**: 6379
- **Purpose**:
  - Caching layer
  - Celery message broker
  - Session storage
  - Result backend

### Frontend Service

#### React Application (`frontend`)
- **Port**: 3000
- **Framework**: React + TypeScript + Vite
- **Hot Reload**: Enabled
- **Features**:
  - Modern UI components
  - API integration
  - Real-time updates

## Data Flow

### Resume Processing Flow

1. **Upload**: User uploads resume via frontend
2. **API**: Frontend sends file to FastAPI backend
3. **Storage**: File stored in S3 (or local storage)
4. **Task Queue**: Celery task queued for processing
5. **Processing**: Celery worker:
   - Extracts text from PDF/DOCX
   - Parses resume data
   - Generates embeddings using BERT
   - Stores in PostgreSQL with vector
6. **Analysis**: AI models analyze resume
7. **Results**: Results cached in Redis
8. **Response**: Frontend polls for results

### Authentication Flow

1. User logs in via frontend
2. Backend validates credentials
3. JWT token generated and returned
4. Token stored in Redis (optional)
5. Token included in subsequent requests
6. Backend validates token on each request

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 14 + pgvector
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Task Queue**: Celery 5.3.4
- **Cache**: Redis 5.0.1
- **ML**: Transformers, SpaCy, Sentence-Transformers
- **Storage**: Boto3 (AWS S3)

### Frontend
- **Framework**: React 18.2
- **Language**: TypeScript 5.3
- **Build Tool**: Vite 5.0
- **HTTP Client**: Axios
- **State Management**: React Query

## Environment Configuration

All configuration is managed through environment variables in `.env`:

- **Database**: Connection strings, credentials
- **Redis**: Connection URL, password
- **Security**: JWT secrets, algorithms
- **AWS**: Access keys, S3 bucket
- **ML**: Model names, paths
- **Celery**: Broker URL, settings

## Health Monitoring

### Health Check Endpoints

- `/health`: Comprehensive health check
  - Database connectivity
  - Redis connectivity
  - Celery worker status
- `/health/live`: Liveness probe (Kubernetes)
- `/health/ready`: Readiness probe (Kubernetes)

### Docker Health Checks

All services include Docker health checks:
- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **Backend**: HTTP `/health` endpoint
- **Frontend**: HTTP connectivity check
- **Celery**: `celery inspect ping`

## Scalability

### Horizontal Scaling

- **Backend**: Multiple FastAPI instances behind load balancer
- **Celery Workers**: Scale workers based on queue depth
- **Redis**: Redis Cluster for high availability
- **PostgreSQL**: Read replicas for read-heavy workloads

### Vertical Scaling

- **Database**: Connection pooling (10-20 connections)
- **Celery**: Worker concurrency (4 workers per instance)
- **Redis**: Memory optimization

## Security

- **Authentication**: JWT tokens with expiration
- **Password Hashing**: bcrypt
- **CORS**: Configurable origins
- **Environment Variables**: Sensitive data in `.env`
- **Database**: Connection encryption (SSL)
- **Redis**: Password authentication

## Development Workflow

1. **Local Development**: Docker Compose for all services
2. **Hot Reload**: Enabled for backend and frontend
3. **Database Migrations**: Alembic for schema changes
4. **Testing**: Pytest for backend, Jest for frontend
5. **Logging**: Structured logging to files and console

## Deployment Considerations

- **Production**: Use production-grade images
- **Secrets**: Use secret management (AWS Secrets Manager, etc.)
- **Monitoring**: Integrate with monitoring tools
- **Backups**: Regular database backups
- **SSL/TLS**: Enable HTTPS in production
- **Rate Limiting**: Implement API rate limiting

