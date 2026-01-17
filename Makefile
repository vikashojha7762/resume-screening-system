.PHONY: help build up down restart logs clean setup install test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Initial setup - copy .env.example to .env
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created from .env.example"; \
		echo "Please update .env with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

install: ## Install dependencies for backend and frontend
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs
	docker-compose logs -f backend

logs-frontend: ## View frontend logs
	docker-compose logs -f frontend

logs-db: ## View database logs
	docker-compose logs -f postgres

logs-redis: ## View Redis logs
	docker-compose logs -f redis

logs-celery: ## View Celery worker logs
	docker-compose logs -f celery-worker

logs-celery-beat: ## View Celery beat logs
	docker-compose logs -f celery-beat

test-connections: ## Test database and Redis connections
	docker-compose exec backend python -m app.core.db_connection_test

restart-celery: ## Restart Celery worker
	docker-compose restart celery-worker celery-beat

clean: ## Remove containers, volumes, and images
	docker-compose down -v
	docker-compose rm -f

test: ## Run tests
	@echo "Running backend tests..."
	cd backend && pytest
	@echo "Running frontend tests..."
	cd frontend && npm test

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MESSAGE="migration message")
	cd backend && alembic revision --autogenerate -m "$(MESSAGE)"

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d resume_screening

