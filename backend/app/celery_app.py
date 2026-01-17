from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "resume_screening",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour
)

# Periodic task schedule (Celery Beat)
celery_app.conf.beat_schedule = {
    "process-pending-resumes": {
        "task": "app.tasks.resume_tasks.process_pending_resumes",
        "schedule": 300.0,  # Every 5 minutes
    },
    "cleanup-old-results": {
        "task": "app.tasks.cleanup_tasks.cleanup_old_results",
        "schedule": 3600.0,  # Every hour
    },
}

