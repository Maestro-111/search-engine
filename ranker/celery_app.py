from celery import Celery

# Create Celery instance
celery_app = Celery(
    "ranker", broker="redis://redis:6379/0", backend="redis://redis:6379/0"
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_ignore_result=False,
    result_expires=3600,  # Results expire after 1 hour
    worker_prefetch_multiplier=0,
    task_acks_late=True,  # Acknowledge tasks after completion
    worker_disable_rate_limits=False,
    task_routes={
        "ranker.tasks.*": {"queue": "ranker"},
    },
    # Auto-discover tasks in the tasks module
    imports=["tasks"],
)
