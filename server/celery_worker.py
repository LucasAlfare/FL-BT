# celery_worker.py
from celery import Celery
from server.lib import single_pipeline

celery_app = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)


@celery_app.task
def heavy_processing_entrypoint(video_id: str) -> dict[str, str]:
    print(f"Starting the job {video_id}...")
    zip_path = single_pipeline(video_id)
    return {"video_id": video_id, "zip_path": zip_path}
