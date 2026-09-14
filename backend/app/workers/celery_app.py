from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "mailing_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.dispatch_mailing_task": {"queue": "dispatch"},
        "app.workers.tasks.send_message_task": {"queue": "sender"},
        "app.workers.tasks.check_scheduled_mailings_task": {"queue": "scheduler"},
    },
    beat_schedule={
        "check-scheduled-mailings-every-30-seconds": {
            "task": "app.workers.tasks.check_scheduled_mailings_task",
            "schedule": 30.0,
        },
    },
)
