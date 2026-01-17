# System Architecture Documentation

## Overview

The Resume Screening System is a microservices-based application built with modern cloud-native technologies.

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Component Architecture](#component-architecture)
- [Database Schema](#database-schema)
- [Deployment Architecture](#deployment-architecture)
- [Data Flow](#data-flow)
- [Security Architecture](#security-architecture)

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Web App    │  │  Mobile App  │  │   API Users  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway / Ingress                     │
│              (Load Balancing, SSL Termination)             │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Frontend   │  │   Backend    │  │  Celery      │
│   Service    │  │   API        │  │  Workers     │
└──────────────┘  └──────────────┘  └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │     S3      │
│  Database    │  │   Cache      │  │   Storage   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Component Architecture

### Frontend Service

- **Technology:** React + TypeScript + Vite
- **State Management:** Redux Toolkit
- **UI Framework:** Material-UI
- **Build:** Docker multi-stage build
- **Deployment:** Nginx serving static files

### Backend API

- **Technology:** FastAPI (Python)
- **Database:** SQLAlchemy 2.0 ORM
- **Authentication:** JWT tokens
- **API Documentation:** OpenAPI/Swagger
- **Deployment:** Uvicorn ASGI server

### Celery Workers

- **Purpose:** Async task processing
- **Tasks:**
  - Resume parsing
  - NLP processing
  - Matching calculations
  - Email notifications
- **Broker:** Redis
- **Result Backend:** Redis

### Database Layer

- **Primary DB:** PostgreSQL 14 with pgvector
- **Caching:** Redis 7
- **Backup:** Automated daily backups to S3

## Database Schema

See [Database Schema Documentation](./database-schema.md) for detailed ER diagrams and table structures.

### Key Tables

- `users` - User accounts and authentication
- `jobs` - Job postings and requirements
- `resumes` - Uploaded resumes and parsed data
- `candidates` - Anonymized candidate records
- `match_results` - Matching scores and rankings
- `processing_queue` - Async task tracking

## Deployment Architecture

### Kubernetes Deployment

```
Namespace: resume-screening
├── Deployments
│   ├── frontend (2 replicas)
│   ├── backend (3-10 replicas, HPA)
│   ├── celery-worker (2-5 replicas, HPA)
│   └── celery-beat (1 replica)
├── StatefulSets
│   └── postgres (1 replica)
├── Services
│   ├── frontend-service
│   ├── backend-service
│   ├── postgres-service
│   └── redis-service
└── Ingress
    └── resume-screening-ingress (SSL/TLS)
```

### Scaling

- **Horizontal Pod Autoscaling:** Based on CPU/Memory
- **Backend:** 3-10 replicas
- **Celery Workers:** 2-5 replicas
- **Frontend:** 2 replicas

## Data Flow

### Resume Processing Flow

```
1. User uploads resume
   ↓
2. File stored in S3
   ↓
3. Celery task created
   ↓
4. Resume parser extracts text
   ↓
5. NLP pipeline processes:
   - Skill extraction
   - Experience parsing
   - Education parsing
   ↓
6. ML models generate embeddings
   ↓
7. Data stored in database
   ↓
8. User notified of completion
```

### Matching Flow

```
1. User initiates matching
   ↓
2. Scoring engine calculates scores:
   - Skills match
   - Experience match
   - Education match
   ↓
3. Ranking engine sorts candidates
   ↓
4. Bias detection runs
   ↓
5. Results stored and returned
```

## Security Architecture

### Authentication Flow

```
1. User submits credentials
   ↓
2. Backend validates with database
   ↓
3. JWT token generated
   ↓
4. Token returned to client
   ↓
5. Client includes token in requests
   ↓
6. Backend validates token
   ↓
7. Request processed if valid
```

### Network Security

- **TLS/SSL:** All traffic encrypted
- **Network Policies:** Pod-to-pod communication restricted
- **WAF:** Web Application Firewall rules
- **Rate Limiting:** API request throttling

### Data Security

- **Encryption at Rest:** Database and S3 encryption
- **Encryption in Transit:** TLS 1.3
- **PII Masking:** Automatic anonymization
- **Access Control:** Role-based access control (RBAC)

## Monitoring and Observability

- **Metrics:** Prometheus
- **Visualization:** Grafana dashboards
- **Logging:** Centralized logging with ELK stack
- **Tracing:** Distributed tracing ready
- **Alerts:** Alertmanager for critical issues

## See Also

- [Database Schema Details](./database-schema.md)
- [Deployment Guide](../operations/deployment.md)
- [Security Guide](../operations/security.md)

