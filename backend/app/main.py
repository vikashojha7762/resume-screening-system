from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import settings
from app.database import engine
from sqlalchemy import text
import redis
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume Screening System API",
    description="AI-powered resume screening and candidate evaluation system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - must be added before other middleware
# For development, allow all origins if needed, but prefer explicit list
cors_origins = settings.CORS_ORIGINS
if settings.DEBUG or settings.ENVIRONMENT == "development":
    # In development, also allow 127.0.0.1 variants
    cors_origins = list(set(cors_origins + [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)


# Helper function to get CORS headers
def get_cors_headers(request: Request) -> dict:
    """Get appropriate CORS headers based on the request origin"""
    origin = request.headers.get("origin")
    if origin and origin in cors_origins:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin",
        }
    return {}


# Global exception handlers to ensure CORS headers are always present
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with CORS headers"""
    headers = get_cors_headers(request)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers"""
    headers = get_cors_headers(request)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers=headers
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with CORS headers"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    headers = get_cors_headers(request)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
        headers=headers
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Resume Screening System API",
        "version": "1.0.0",
        "docs": "/docs",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
    
    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["database"] = "disconnected"
        health_status["status"] = "unhealthy"
    
    # Check Redis connection
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        health_status["redis"] = "disconnected"
        health_status["status"] = "unhealthy"
    
    # Check Celery worker
    try:
        from app.celery_app import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            health_status["celery"] = "connected"
            health_status["celery_workers"] = len(active_workers)
        else:
            health_status["celery"] = "no_workers"
    except Exception as e:
        logger.error(f"Celery health check failed: {str(e)}")
        health_status["celery"] = "disconnected"
    
    status_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        # Check database
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Check Redis
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            content={"status": "not_ready", "error": str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    logger.info(f"CORS allowed origins: {cors_origins}")
    logger.info(f"Environment: {settings.ENVIRONMENT}, Debug: {settings.DEBUG}")
    try:
        from app.database import init_db
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}", exc_info=True)


# Include routers
from app.api.v1 import auth, jobs, resumes, results, interviews, candidates as candidates_api

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(jobs.router, prefix=settings.API_V1_PREFIX)
app.include_router(resumes.router, prefix=settings.API_V1_PREFIX)
app.include_router(results.router, prefix=settings.API_V1_PREFIX)
app.include_router(interviews.router, prefix=settings.API_V1_PREFIX)
app.include_router(candidates_api.router, prefix=settings.API_V1_PREFIX)

