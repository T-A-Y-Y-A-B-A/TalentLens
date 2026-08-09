from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "talentlens",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.services.email", "app.workers.tasks", "app.workers.tasks.resume_parser", "app.workers.tasks.matching", "app.workers.tasks.email"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"]
)
