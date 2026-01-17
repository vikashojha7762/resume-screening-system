# AI-Powered Resume Screening System

A comprehensive full-stack application for automated resume screening using AI/ML technologies. This system helps HR departments and recruiters efficiently process and evaluate job applications.

## 🚀 Features

- **AI-Powered Analysis**: Automated resume parsing and candidate evaluation using BERT and SpaCy
- **Smart Matching**: Intelligent job-candidate matching based on skills and experience with vector similarity
- **Async Processing**: Celery workers for background task processing
- **Caching**: Redis for high-performance caching and session management
- **Vector Database**: PostgreSQL 14 with pgvector extension for semantic search
- **User Management**: Secure authentication and role-based access control
- **Dashboard**: Real-time analytics and insights
- **API-First Architecture**: RESTful API for easy integration
- **Modern UI**: Responsive React-based frontend with hot reload
- **Health Checks**: Comprehensive health monitoring for all services

## 📋 Prerequisites

- Docker and Docker Compose
- Git
- Make (optional, for using Makefile commands)

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd resume-screening-system
```

### 2. Setup Environment

```bash
# Copy environment variables
cp .env.example .env

# Edit .env file with your configuration
# Make sure to change SECRET_KEY and other sensitive values
```

### 3. Start Services

Using Docker Compose:
```bash
docker-compose up -d
```

Or using Make:
```bash
make setup
make build
make up
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 📁 Project Structure

```
resume-screening-system/
├── backend/          # FastAPI backend application
│   ├── app/         # Main application code
│   │   ├── core/    # Core utilities (config, security, redis)
│   │   ├── api/     # API routes
│   │   ├── models/  # Database models
│   │   ├── schemas/ # Pydantic schemas
│   │   └── tasks/   # Celery tasks
│   ├── alembic/     # Database migrations
│   └── requirements.txt
├── frontend/        # React TypeScript frontend
│   ├── src/         # Source code
│   └── public/      # Static assets
├── scripts/         # Utility scripts
│   └── init-db.sql  # Database initialization
├── docker-compose.yml
└── README.md
```

## 🐳 Services

The application runs the following services:

- **PostgreSQL 14**: Database with pgvector extension for vector similarity search
- **Redis 7**: Caching and message broker for Celery
- **FastAPI Backend**: Main API server with hot reload
- **Celery Worker**: Background task processing
- **Celery Beat**: Scheduled task runner
- **React Frontend**: User interface with hot reload

## 🔧 Development

### Backend Development

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

### Frontend Development

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm start
```

### Database Migrations

```bash
# Create a new migration
make migrate-create MESSAGE="your migration message"

# Apply migrations
make migrate
```

## 🐳 Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Access container shell
docker-compose exec backend /bin/bash
```

## 📝 Available Make Commands

- `make setup` - Initial setup (creates .env file)
- `make install` - Install all dependencies
- `make build` - Build Docker images
- `make up` - Start all services
- `make down` - Stop all services
- `make logs` - View all logs
- `make migrate` - Run database migrations
- `make test` - Run tests
- `make clean` - Remove containers and volumes

## 🔐 Environment Variables

Comprehensive environment variables (see `.env.example` for full list):

### Database
- `DATABASE_URL` - PostgreSQL connection string
- `DB_USER`, `DB_PASSWORD`, `DB_NAME` - Database credentials

### Redis
- `REDIS_URL` - Redis connection string
- `REDIS_PASSWORD` - Redis password

### Security
- `SECRET_KEY` - JWT secret key (change in production!)
- `ALGORITHM` - JWT algorithm
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration

### AWS
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` - AWS credentials
- `AWS_S3_BUCKET` - S3 bucket for file storage

### ML/AI
- `BERT_MODEL_NAME` - BERT model for NLP
- `SPACY_MODEL` - SpaCy model name
- `OPENAI_API_KEY` - OpenAI API key (optional)

### Application
- `DEBUG` - Debug mode
- `ENVIRONMENT` - Environment (development/production)
- `REACT_APP_API_URL` - Backend API URL

## 🧪 Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions, please open an issue on GitHub.

## 🗺️ Roadmap

- [ ] Resume parsing and extraction
- [ ] AI-powered candidate scoring
- [ ] Job-candidate matching algorithm
- [ ] Email notifications
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Integration with job boards

