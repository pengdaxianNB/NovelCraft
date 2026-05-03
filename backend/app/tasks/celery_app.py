from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "novel_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.generation_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    task_annotations={
        "app.tasks.generation_tasks.*": {"max_retries": 3, "default_retry_delay": 60},
    },
)

# Periodic task: scan for scheduled novels every 5 minutes
celery_app.conf.beat_schedule = {
    "check-scheduled-novels": {
        "task": "app.tasks.generation_tasks.check_scheduled_novels",
        "schedule": crontab(minute="*/5"),
    },
}
