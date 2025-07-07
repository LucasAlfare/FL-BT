# server/celery_app.py

from celery import Celery

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",  # configure Redis broker
    backend="redis://localhost:6379/0"  # result backend
)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True
