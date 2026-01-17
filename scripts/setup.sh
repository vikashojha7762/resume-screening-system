#!/bin/bash

# Resume Screening System Setup Script
# This script helps set up the development environment

set -e

echo "🚀 Setting up Resume Screening System..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ .env file created. Please update it with your configuration."
    else
        echo "⚠️  .env.example not found. Creating basic .env file..."
        cat > .env << EOF
# Database Configuration
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=resume_screening
DB_HOST=postgres
DB_PORT=5432

# Backend Configuration
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
BACKEND_PORT=8000

# Frontend Configuration
FRONTEND_PORT=3000
REACT_APP_API_URL=http://localhost:8000
EOF
        echo "✅ Basic .env file created."
    fi
else
    echo "✅ .env file already exists."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo ""
echo "🐳 Docker and Docker Compose are installed."
echo ""

# Check if node_modules exist in frontend
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo "✅ Frontend dependencies installed."
else
    echo "✅ Frontend dependencies already installed."
fi

# Check if virtual environment exists in backend
if [ ! -d "backend/venv" ] && [ ! -d "backend/.venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv || python -m venv venv
    source venv/bin/activate || source venv/Scripts/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
    echo "✅ Backend virtual environment created and dependencies installed."
else
    echo "✅ Backend virtual environment already exists."
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review and update the .env file with your configuration"
echo "2. Run 'docker-compose up -d' to start the services"
echo "3. Visit http://localhost:3000 for the frontend"
echo "4. Visit http://localhost:8000/docs for the API documentation"
echo ""

