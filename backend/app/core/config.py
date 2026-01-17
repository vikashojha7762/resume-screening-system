from pydantic_settings import BaseSettings
from typing import List, Optional
from urllib.parse import quote_plus
from pydantic import computed_field


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Resume Screening System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Database
    DB_USER: str = "postgres"
    DB_PASSWORD: Optional[str] = None  # Must be set via environment variable
    DB_NAME: str = "resume_screening"
    DB_HOST: str = "localhost"  # Use 'postgres' for Docker, 'localhost' for local development
    DB_PORT: int = 5433
    # DATABASE_URL will be computed from components to handle password encoding
    DATABASE_URL: Optional[str] = None
    
    # Redis
    REDIS_URL: Optional[str] = None  # Must be set via environment variable (e.g., redis://:password@host:port/db)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None  # Must be set via environment variable
    REDIS_DB: int = 0
    
    # Security
    SECRET_KEY: Optional[str] = None  # Must be set via environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]
    
    # URLs
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: Optional[str] = None
    AWS_S3_RESUME_PREFIX: str = "resumes/"
    AWS_S3_PROCESSED_PREFIX: str = "processed/"
    
    # Machine Learning Configuration
    BERT_MODEL_NAME: str = "bert-base-uncased"
    BERT_MODEL_PATH: str = "models/bert-base-uncased"
    SPACY_MODEL: str = "en_core_web_sm"
    SPACY_MODEL_PATH: str = "models/en_core_web_sm"
    USE_GPU: bool = False
    ML_CACHE_TTL: int = 3600
    
    # Celery Configuration
    CELERY_BROKER_URL: Optional[str] = None  # Must be set via environment variable (defaults to REDIS_URL if not set)
    CELERY_RESULT_BACKEND: Optional[str] = None  # Must be set via environment variable (defaults to REDIS_URL if not set)
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000
    
    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "noreply@resumescreening.com"
    EMAIL_FROM_NAME: str = "Resume Screening System"
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "doc", "docx", "txt"]
    UPLOAD_DIR: str = "uploads"
    
    # AI/ML API Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    
    # Monitoring & Logging
    SENTRY_DSN: Optional[str] = None
    LOG_FILE_PATH: str = "logs/app.log"
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def model_post_init(self, __context):
        # Always recompute DATABASE_URL from components to ensure proper password encoding
        # This fixes issues where DATABASE_URL from env has unencoded special characters
        # For local development, use localhost instead of Docker hostname
        
        # Use DATABASE_URL from env if provided, otherwise construct from components
        if self.DATABASE_URL:
            pass  # Already set from environment
        elif self.DB_PASSWORD:
            db_host = "localhost" if self.DB_HOST == "postgres" and not self.ENVIRONMENT == "docker" else self.DB_HOST
            encoded_password = quote_plus(self.DB_PASSWORD)
            computed_url = f"postgresql://{self.DB_USER}:{encoded_password}@{db_host}:{self.DB_PORT}/{self.DB_NAME}"
            object.__setattr__(self, 'DATABASE_URL', computed_url)
        
        # Set default Celery URLs from REDIS_URL if not explicitly set
        if not self.CELERY_BROKER_URL and self.REDIS_URL:
            object.__setattr__(self, 'CELERY_BROKER_URL', self.REDIS_URL)
        if not self.CELERY_RESULT_BACKEND and self.REDIS_URL:
            object.__setattr__(self, 'CELERY_RESULT_BACKEND', self.REDIS_URL)


settings = Settings()

