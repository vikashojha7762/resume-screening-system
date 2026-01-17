# Quick Start Guide

## Prerequisites
- Docker and Docker Compose installed
- Git installed

## Setup Steps

### 1. Environment Setup
```bash
# Copy environment file
cp .env.example .env

# Edit .env with your settings (especially SECRET_KEY)
```

### 2. Start with Docker Compose
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Using Make Commands (if Make is installed)
```bash
make setup    # Create .env file
make build    # Build Docker images
make up       # Start services
make logs     # View logs
make down     # Stop services
```

### 5. Manual Setup (without Docker)
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

## Next Steps
1. Review the README.md for detailed documentation
2. Set up your database migrations: `cd backend && alembic upgrade head`
3. Start building your features!

