from celery import Celery

from server.lib import single_pipeline

celery_app = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)


@celery_app.task
def heavy_processing_entrypoint(job_id: str) -> str:
    print(f"Starting the job {job_id}...")
    return single_pipeline(job_id)
