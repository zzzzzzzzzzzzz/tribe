from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.tasks"],
)

celery_app.conf.update(
    result_expires=3600,
    beat_schedule={
        "cleanup-expired-provider-attachments-daily": {
            "task": "app.tasks.tasks.cleanup_expired_provider_attachments",
            "schedule": 60 * 60 * 24,
        },
    },
)
